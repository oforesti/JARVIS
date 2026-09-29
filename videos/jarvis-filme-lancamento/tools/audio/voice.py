"""Narração do filme JARVIS: SCRIPT.md → falas tratadas + tempo de cada palavra.

Uso:
  python voice.py <SCRIPT.md> <saida-dir> --kokoro <dir-kokoro> --parakeet <dir-parakeet>
                  [--voice pm_alex] [--speed 0.97]

Para cada linha do roteiro: gera com Kokoro (pt-BR), remove silêncios das pontas, converte para
48 kHz, aplica a cadeia de voz (HPF, EQ, de-esser, compressão, nível), mede as palavras com
Parakeet e grava `line-NN.flac` + `voice.json` (texto exibido, duração, palavras com início/fim).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

import dsp
from dsp import SR

VOICES = {"pf_dora": 42, "pm_alex": 43, "pm_santa": 44}

# grafias só para a fala (a legenda usa o texto original)
RESPELL = [
    (r"\bJARVIS\b", "Djárvis"),
    (r"\bULTRON\b", "Últron"),
    (r"\bPython\b", "Páiton"),
    (r"\bAndroid\b", "Ândroid"),
]


def parse_script(path: Path) -> list[dict]:
    lines, cur = [], None
    for raw in path.read_text().splitlines():
        m = re.match(r"^## Line (\d+) — (.+?) \(Frame (\d+)\)", raw)
        if m:
            cur = {"n": int(m.group(1)), "label": m.group(2), "frame": int(m.group(3)), "text": ""}
            lines.append(cur)
            continue
        if cur is not None and raw.startswith("    ") and raw.strip():
            cur["text"] = (cur["text"] + " " + raw.strip()).strip()
    return lines


def tts_text(text: str) -> str:
    out = text
    for pat, rep in RESPELL:
        out = re.sub(pat, rep, out)
    return out


def trim(x: np.ndarray, sr: int, floor_db: float = -40.0, pad_in: float = 0.04, pad_out: float = 0.12) -> np.ndarray:
    env = np.abs(x)
    win = max(1, int(0.01 * sr))
    env = np.convolve(env, np.ones(win) / win, mode="same")
    thr = env.max() * 10 ** (floor_db / 20)
    idx = np.nonzero(env > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad_in * sr))
    b = min(len(x), idx[-1] + int(pad_out * sr))
    return x[a:b]


def deess(x: np.ndarray, thresh_db: float = -26.0, ratio: float = 4.0) -> np.ndarray:
    """De-esser dinâmico: comprime só a banda 5–9 kHz quando ela passa do limiar."""
    band = dsp.svf(x, 6800, 0.9, "bp")
    env = np.abs(band)
    w = int(0.004 * SR)
    env = np.convolve(env, np.ones(w) / w, mode="same")
    lvl = 20 * np.log10(env + 1e-9)
    over = np.maximum(0, lvl - thresh_db)
    gain_db = -over * (1 - 1 / ratio)
    g = 10 ** (gain_db / 20)
    return x - band * (1 - g)


def process(x24: np.ndarray) -> np.ndarray:
    x = resample_poly(x24, 2, 1)  # 24 k → 48 k
    x = dsp.hp(x, 75)[0]
    x = dsp.eq(x, peaks=[(210, -2.0, 1.0), (3600, 2.2, 0.9)], high_shelf=(10500, 1.5))[0]
    x = deess(x)
    x = dsp.compress(x, threshold=-22, ratio=2.4, attack=8, release=140)[0]
    x = dsp.lp(x, 15500)[0]
    return x


def rms_db(x: np.ndarray) -> float:
    env = np.abs(x)
    active = env[env > env.max() * 0.05]
    return 20 * np.log10(np.sqrt(np.mean(active ** 2)) + 1e-12)


def main(argv: list[str]) -> None:
    import sherpa_onnx as so
    import soundfile as sf

    script = Path(argv[1])
    out = Path(argv[2])
    kdir = Path(argv[argv.index("--kokoro") + 1])
    pdir = Path(argv[argv.index("--parakeet") + 1])
    voice = argv[argv.index("--voice") + 1] if "--voice" in argv else "pm_alex"
    speed = float(argv[argv.index("--speed") + 1]) if "--speed" in argv else 0.97
    only = [int(v) for v in argv[argv.index("--only") + 1].split(",")] if "--only" in argv else None
    split = [int(v) for v in argv[argv.index("--split") + 1].split(",")] if "--split" in argv else []
    out.mkdir(parents=True, exist_ok=True)

    tts = so.OfflineTts(so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(
        kokoro=so.OfflineTtsKokoroModelConfig(
            model=str(kdir / "model.onnx"), voices=str(kdir / "voices.bin"), tokens=str(kdir / "tokens.txt"),
            data_dir=str(kdir / "espeak-ng-data"), lexicon=str(kdir / "lexicon-us-en.txt"), lang="pt-br"),
        num_threads=4, provider="cpu"), max_num_sentences=1))
    rec = so.OfflineRecognizer.from_transducer(
        encoder=str(pdir / "encoder.int8.onnx"), decoder=str(pdir / "decoder.int8.onnx"),
        joiner=str(pdir / "joiner.int8.onnx"), tokens=str(pdir / "tokens.txt"),
        model_type="nemo_transducer", num_threads=4)

    meta_path = out / "voice.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"voice": voice, "lines": []}
    meta["voice"], meta["speed"] = voice, speed
    by_n = {f"{l['n']}{chr(96 + l['part']) if l.get('part') else ''}": l for l in meta["lines"]}
    target = -20.0
    expanded = []
    for line in parse_script(script):
        if line["n"] in split:
            parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", line["text"]) if p.strip()]
            for k, ptxt in enumerate(parts):
                expanded.append({**line, "text": ptxt, "part": k + 1, "parent_text": line["text"]})
        else:
            expanded.append(line)
    for line in expanded:
        if only and line["n"] not in only:
            continue
        a = tts.generate(tts_text(line["text"]), sid=VOICES[voice], speed=speed)
        x24 = trim(np.array(a.samples, dtype=np.float64), a.sample_rate)
        x = process(x24)
        x *= 10 ** ((target - rms_db(x)) / 20)
        peak = np.abs(x).max()
        if peak > 0.89:
            x *= 0.89 / peak
        part = line.get("part")
        name = f"line-{line['n']:02d}{chr(96 + part) if part else ''}.flac"
        sf.write(str(out / name), x.astype(np.float32), SR, format="FLAC", subtype="PCM_24")
        # palavras (Parakeet em 16 kHz)
        x16 = resample_poly(x, 1, 3).astype(np.float32)
        st = rec.create_stream()
        st.accept_waveform(16000, x16)
        rec.decode_stream(st)
        r = st.result
        toks, ts = list(r.tokens), list(r.timestamps)
        words, cur, t0 = [], "", None
        for tok, t in zip(toks, ts):
            if tok.startswith("▁") or tok.startswith(" "):
                if cur:
                    words.append({"asr": cur, "start": t0})
                cur, t0 = tok.lstrip("▁ "), t
            else:
                cur += tok
                t0 = t if t0 is None else t0
        if cur:
            words.append({"asr": cur, "start": t0})
        dur = len(x) / SR
        for i, w in enumerate(words):
            w["end"] = words[i + 1]["start"] if i + 1 < len(words) else dur
        disp = line["text"].split()
        # alinha palavras exibidas às medidas (mesma contagem → 1:1; senão proporcional)
        if len(words) == len(disp):
            aligned = [{"text": d, "start": round(w["start"], 3), "end": round(w["end"], 3)} for d, w in zip(disp, words)]
        else:
            chars = np.cumsum([len(d) + 1 for d in disp])
            tot = chars[-1]
            first = words[0]["start"] if words else 0.0
            last = words[-1]["end"] if words else dur
            aligned = []
            prev = first
            for d, c in zip(disp, chars):
                end = first + (last - first) * c / tot
                aligned.append({"text": d, "start": round(prev, 3), "end": round(end, 3)})
                prev = end
        entry = {"n": line["n"], "frame": line["frame"], "label": line["label"], "text": line["text"],
                 "file": name, "duration": round(dur, 3), "asr": r.text, "words": aligned}
        if part:
            entry["part"] = part
        key = f"{line['n']}{chr(96 + part) if part else ''}"
        by_n[key] = entry
        print(f"L{key:4s}  {dur:5.2f}s  {line['text']}\n      asr: {r.text}")
    if split:
        for n in split:
            by_n.pop(str(n), None)
    meta["lines"] = [by_n[k] for k in sorted(by_n, key=lambda k: (int(re.match(r"\d+", k).group()), k))]
    meta["total_speech"] = round(sum(l["duration"] for l in meta["lines"]), 2)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print("total de fala:", meta["total_speech"], "s")


if __name__ == "__main__":
    main(sys.argv)
