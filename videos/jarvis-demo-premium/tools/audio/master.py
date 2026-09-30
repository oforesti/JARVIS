"""Masterização final do filme: mede a mixagem do render, equilibra o volume e aplica teto de pico.

Uso:
  python master.py <render.mp4> <saida.mp4> [--target -14] [--tp -1.0] [--report-only]
                   [--gain-db G --no-voice]   (versão sem narração com o mesmo ganho da narrada)
                   [--voice-html index.html]  (recut: a voz vem dos clipes "voiceover" da composição)

- Decodifica o áudio do render (48 kHz, float).
- Relatório: loudness integrado, pico real (4×), e o equilíbrio voz × trilha em cada fala
  (a voz é remontada a partir de assets/voice + timeline.json; a trilha é o resíduo mix − voz).
- Ganho até o alvo (padrão −14 LUFS, web) e limitador com lookahead e true peak (padrão −1 dBTP).
- Remux: vídeo copiado sem reencode, áudio AAC 320 kb/s, faststart.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

import dsp
from dsp import SR

ROOT = Path(__file__).resolve().parents[2]


def decode(path: Path) -> np.ndarray:
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "2", "-ar", str(SR),
                        "-c:a", "pcm_f32le", str(wav)], check=True)
        x, sr = sf.read(str(wav), dtype="float64", always_2d=True)
    assert sr == SR
    return x.T.copy()


def true_peak_db(x: np.ndarray) -> float:
    from scipy.signal import resample_poly
    up = resample_poly(x, 4, 1, axis=1)
    return 20 * np.log10(np.abs(up).max() + 1e-12)


def voice_stem(n: int) -> tuple[np.ndarray, dict]:
    tl = json.loads((ROOT / "timeline.json").read_text())
    out = np.zeros((2, n))
    for v in tl["vo"]:
        y, sr = sf.read(str(ROOT / v["file"]), dtype="float64", always_2d=True)
        assert sr == SR
        y = y.T
        if y.shape[0] == 1:
            y = np.vstack([y, y])
        a = int(round(v["start"] * SR))
        b = min(n, a + y.shape[1])
        if a < n:
            out[:, a:b] += y[:, : b - a]
    return out, tl


def voice_from_html(n: int, comp: Path) -> tuple[np.ndarray, dict]:
    """Voz remontada a partir dos <audio data-audio-group="voiceover"> da composição; falas por atividade."""
    import html as _h
    import re
    out = np.zeros((2, n))
    base = comp.resolve().parent
    for m in re.finditer(r"<audio\b[^>]*>", comp.read_text()):
        tag = m.group(0)
        if 'data-audio-group="voiceover"' not in tag:
            continue
        g = lambda k, d=None: (re.search(k + r'="([^"]*)"', tag) or [None, d])[1]
        t0, dur, m0, vol = float(g("data-start")), float(g("data-duration")), float(g("data-media-start", 0)), float(g("data-volume", 1))
        y, sr = sf.read(str(base / _h.unescape(g("src"))), dtype="float64", always_2d=True, start=int(m0 * SR), stop=int((m0 + dur) * SR))
        assert sr == SR
        a = int(round(t0 * SR))
        b = min(n, a + y.shape[0])
        out[:, a:b] += vol * y.T[:, : b - a]
    # falas = trechos com energia (janelas de 50 ms a menos de 28 dB do nível típico da voz), pausas < 0,3 s unidas
    hop = int(0.05 * SR)
    rms = np.sqrt(np.mean(out[0, : n // hop * hop].reshape(-1, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    on = db > np.percentile(db[db > -90], 90) - 28 if np.any(db > -90) else np.zeros_like(db, bool)
    segs, k = [], 0
    while k < len(on):
        if on[k]:
            j = k
            while j < len(on) and (on[j] or np.any(on[j:j + 6])):
                j += 1
            segs.append({"id": f"f{len(segs) + 1:03d}", "start": k * 0.05, "end": j * 0.05})
            k = j
        k += 1
    return out, {"vo": segs}


def align(mix: np.ndarray, ref: np.ndarray, around: float, span: float = 0.25) -> int:
    """Atraso (amostras) do ref dentro do mix, perto de `around` s, por correlação cruzada."""
    a = int((around - span) * SR)
    b = int((around + span + 1.0) * SR)
    m = mix[0, a:b]
    r = ref[0, a + int(span * SR): a + int(span * SR) + int(1.0 * SR)]
    best, lag = -1.0, 0
    for d in range(-int(span * SR), int(span * SR), 8):
        seg = m[int(span * SR) + d: int(span * SR) + d + r.shape[0]]
        if seg.shape[0] < r.shape[0]:
            continue
        c = float(np.dot(seg, r))
        if c > best:
            best, lag = c, d
    return lag


def lufs(x: np.ndarray) -> float:
    try:
        return dsp.loudness_lufs(x)
    except Exception:
        return float("-inf")


def report(mix: np.ndarray, comp: Path | None = None) -> None:
    n = mix.shape[1]
    vo, tl = voice_from_html(n, comp) if comp else voice_stem(n)
    lag = align(mix, vo, tl["vo"][min(2, len(tl["vo"]) - 1)]["start"])
    if lag:
        vo = np.roll(vo, lag, axis=1)
    bed = mix - vo
    print(f"  alinhamento da voz: {lag / SR * 1000:+.1f} ms")
    print(f"  mix: {lufs(mix):6.1f} LUFS integrado · pico real {true_peak_db(mix):+.2f} dBTP")
    print(f"  voz sozinha: {lufs(vo):6.1f} LUFS · trilha+SFX (resíduo): {lufs(bed):6.1f} LUFS")
    print("  por fala (LUFS da voz / da trilha no mesmo trecho → folga):")
    gaps = []
    for v in tl["vo"]:
        a, b = int(v["start"] * SR), int(v["end"] * SR)
        if b - a < int(0.45 * SR):
            continue
        lv, lb = lufs(vo[:, a:b]), lufs(bed[:, a:b])
        gaps.append((lv - lb, v["start"]))
        if len(tl["vo"]) <= 40:
            print(f"    {v['id']:5s} {v['start']:6.2f}s  voz {lv:6.1f}  trilha {lb:6.1f}  folga {lv - lb:5.1f} dB")
    if gaps:
        g = np.array([x for x, _ in gaps])
        print(f"  {len(g)} falas · folga média {g.mean():.1f} dB (mín {g.min():.1f}, máx {g.max():.1f})")
        print("  mais apertadas: " + ", ".join(f"{t:.1f}s {x:.1f} dB" for x, t in sorted(gaps)[:6]))


def master(mix: np.ndarray, target: float, tp: float, fixed_gain: float | None = None) -> tuple[np.ndarray, float]:
    """Ganho até o alvo (ou ganho fixo, para versões que precisam casar com outra) + teto de pico."""
    if fixed_gain is not None:
        return dsp.limit(mix * 10 ** (fixed_gain / 20), threshold=tp - 0.3, release=120, lookahead_ms=6.0), fixed_gain
    y, total = mix.copy(), 0.0
    for _ in range(3):
        g = target - lufs(y)
        total += g
        y = dsp.limit(y * 10 ** (g / 20), threshold=tp - 0.3, release=120, lookahead_ms=6.0)
        if abs(lufs(y) - target) < 0.15:
            break
    return y, total


def main(argv: list[str]) -> None:
    src, dst = Path(argv[1]), Path(argv[2])
    target = float(argv[argv.index("--target") + 1]) if "--target" in argv else -14.0
    tp = float(argv[argv.index("--tp") + 1]) if "--tp" in argv else -1.0
    fixed = float(argv[argv.index("--gain-db") + 1]) if "--gain-db" in argv else None
    mix = decode(src)
    print(f"render: {src.name} · {mix.shape[1] / SR:.2f}s")
    if "--no-voice" not in argv:
        report(mix, Path(argv[argv.index("--voice-html") + 1]) if "--voice-html" in argv else None)
    else:
        print(f"  mix: {lufs(mix):6.1f} LUFS integrado · pico real {true_peak_db(mix):+.2f} dBTP")
    if "--report-only" in argv:
        return
    y, gain = master(mix, target, tp, fixed)
    print(f"master: ganho {gain:+.2f} dB · {lufs(y):.2f} LUFS · pico real {true_peak_db(y):+.2f} dBTP")
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "m.wav"
        sf.write(str(wav), y.T.astype(np.float32), SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-movflags", "+faststart",
                        "-shortest", str(dst)], check=True)
    chk = decode(dst)
    print(f"entregue: {dst.name} · {lufs(chk):.2f} LUFS · pico real {true_peak_db(chk):+.2f} dBTP (após AAC)")


if __name__ == "__main__":
    main(sys.argv)
