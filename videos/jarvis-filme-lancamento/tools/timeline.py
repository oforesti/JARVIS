"""Linha do tempo do filme — fonte única de verdade para cenas, voz, legendas, trilha e SFX.

Uso: python tools/timeline.py            (lê assets/voice/voice.json, escreve timeline.json)

Tudo que acontece em momentos importantes cai na grade da trilha (100 BPM, tempo forte da
revelação em 5,6 s): as falas começam num tempo, os cortes caem em tempos ou compassos.
As cenas leem `window.JT` (injetado no index.html) para sincronizar animações com palavras.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BPM = 100.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
ANCHOR = 5.6  # ignição do núcleo = tempo forte 1 da trilha
HALF = BEAT / 2  # colcheia: grade das entradas de fala


def snap(t: float, grid: float = HALF, mode: str = "near") -> float:
    k = (t - ANCHOR) / grid
    k = math.ceil(k - 1e-6) if mode == "up" else round(k)
    return round(ANCHOR + k * grid, 3)


def main() -> None:
    voice = json.loads((ROOT / "assets/voice/voice.json").read_text())
    L = {}
    for l in voice["lines"]:
        key = f"L{l['n']:02d}{chr(96 + l['part']) if l.get('part') else ''}"
        L[key] = l

    vo, frames, marks = [], [], {}

    def say(key: str, at: float, frame: str, caption: bool = True) -> float:
        l = L[key]
        words = [{"text": w["text"], "start": round(at + w["start"], 3), "end": round(at + w["end"], 3)} for w in l["words"]]
        vo.append({"id": key, "file": f"assets/voice/{l['file']}", "start": round(at, 3), "duration": l["duration"],
                   "end": round(at + l["duration"], 3), "frame": frame, "text": l["text"], "caption": caption,
                   "words": words})
        return at + l["duration"]

    def word(key: str, text: str, k: int = 0) -> float:
        for v in vo:
            if v["id"] == key:
                hits = [w for w in v["words"] if w["text"].lower().strip(".,:;!?").startswith(text.lower())]
                return hits[k]["start"]
        raise KeyError((key, text))

    # ---------------------------------------------------------------- F01 abertura
    marks["reveal"] = ANCHOR
    say("L01", 0.80, "f01")
    f01_end = ANCHOR + 2 * BAR  # 10.4: mergulho no orb e corte casado
    frames.append({"id": "f01-abertura", "start": 0.0, "end": f01_end})

    # ---------------------------------------------------------------- F02 promessa
    t = f01_end
    e = say("L02", snap(t + 0.6), "f02", caption=False)
    e = say("L03", snap(e + 0.45, mode="up"), "f02")
    f02_end = snap(e + 0.3, mode="up")
    frames.append({"id": "f02-promessa", "start": t, "end": f02_end})

    # ---------------------------------------------------------------- F03 ações (verbos)
    t = f02_end
    e = say("L04", snap(t + 0.3, mode="up"), "f03", caption=False)
    at = snap(e + 0.3, grid=BEAT, mode="up")
    verbs = []
    for k in "abcdefg":
        key = f"L05{k}"
        e = say(key, at, "f03", caption=False)
        verbs.append({"key": key, "at": at, "end": e})
        at = snap(e - 0.04, mode="up")
    marks["verbs"] = verbs
    f03_end = snap(e + 0.45, mode="up")
    frames.append({"id": "f03-acoes", "start": t, "end": f03_end})

    # ---------------------------------------------------------------- F04 funções
    t = f03_end
    e = say("L06", snap(t + 0.45, mode="up"), "f04")
    marks["count_start"] = word("L06", "duzentas")
    marks["areas_at"] = word("L06", "dezoito")
    e = say("L07", snap(e + 0.35, mode="up"), "f04")
    marks["risk_at"] = word("L07", "risco")
    f04_end = snap(e + 0.55, mode="up")
    frames.append({"id": "f04-funcoes", "start": t, "end": f04_end})

    # ---------------------------------------------------------------- F05 encadeia
    t = f04_end
    e = say("L08", snap(t + 0.45, mode="up"), "f05", caption=False)  # a tipografia da cena é a fala
    marks["type_start"] = snap(e + 0.2, mode="up")
    marks["type_end"] = round(marks["type_start"] + 2.3, 3)
    e = say("L09", snap(marks["type_end"] + 0.25, mode="up"), "f05")
    marks["step1_at"] = word("L09", "cria")
    marks["step2_at"] = word("L09", "acende")
    f05_end = snap(e + 0.5, mode="up")
    frames.append({"id": "f05-encadeia", "start": t, "end": f05_end})

    # ---------------------------------------------------------------- F06 Elo (clímax)
    t = snap(f05_end + 0.4, grid=BAR, mode="up")  # entra num compasso, depois de um respiro
    marks["breath_elo"] = [f05_end, t]
    frames[-1]["end"] = t  # a cena 5 segura o último quadro durante o respiro
    e = say("L10", snap(t + 0.4, mode="up"), "f06")
    e = say("L11", snap(e + 0.3, mode="up"), "f06")
    marks["elo_wake"] = word("L11", "ligue")
    marks["elo_screen"] = word("L11", "use")
    marks["elo_share"] = word("L11", "compartilhe")
    f06_end = snap(e + 0.7, mode="up")
    frames.append({"id": "f06-elo", "start": t, "end": f06_end})

    # ---------------------------------------------------------------- F07 ferramenta
    t = f06_end
    e = say("L12", snap(t + 0.45, mode="up"), "f07")
    marks["code_start"] = word("L12", "escreve")
    e = say("L13", snap(e + 0.8, mode="up"), "f07")
    marks["review_at"] = word("L13", "revisa")
    marks["approve_at"] = word("L13", "aprova")
    f07_end = snap(e + 1.0, mode="up")
    frames.append({"id": "f07-ferramenta", "start": t, "end": f07_end})

    # ---------------------------------------------------------------- F08 personalidades
    t = f07_end
    e = say("L14", snap(t + 0.45, mode="up"), "f08", caption=False)
    e = say("L15", snap(e + 0.3, mode="up"), "f08")
    marks["ultron_at"] = word("L15", "ULTRON")
    f08_end = snap(e + 0.6, mode="up")
    frames.append({"id": "f08-personas", "start": t, "end": f08_end})

    # ---------------------------------------------------------------- F09 final
    t = f08_end
    marks["final_breath"] = [t, round(t + 0.6, 3)]
    e = say("L16", snap(t + 0.75, mode="up"), "f09", caption=False)  # assinatura: a tipografia é a fala
    ign = snap(e + 0.5, grid=BAR, mode="up")
    marks["final_ignition"] = ign
    e = say("L17", snap(ign + 1.2, mode="up"), "f09", caption=False)
    e = say("L18", snap(e + 0.45, mode="up"), "f09", caption=False)
    marks["cta_at"] = vo[-1]["start"]
    end = round(e + 2.6, 3)
    frames.append({"id": "f09-final", "start": t, "end": end})

    for f in frames:
        f["duration"] = round(f["end"] - f["start"], 3)
        f["file"] = f"compositions/frames/{f['id'][1:3]}-{f['id'].split('-', 1)[1]}.html"
        f["comp"] = f["id"]

    tl = {"bpm": BPM, "beat": BEAT, "bar": BAR, "anchor": ANCHOR, "duration": end,
          "frames": frames, "vo": vo, "marks": marks}
    (ROOT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    print(f"duração {end:.2f}s · fala {sum(v['duration'] for v in vo):.1f}s")
    for f in frames:
        print(f"  {f['id']:16s} {f['start']:6.2f} → {f['end']:6.2f}  ({f['duration']:.2f}s)")
    for v in vo:
        print(f"    {v['id']:5s} {v['start']:6.2f}–{v['end']:6.2f}  {'' if v['caption'] else '[sem legenda] '}{v['text']}")


if __name__ == "__main__":
    main()
