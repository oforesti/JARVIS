"""Trilha longa (13 min) em blocos: cada bloco é renderizado com o motor de music.py e emendado
com crossfade nas trocas de seção, para caber na memória. Nível final único (−18 LUFS).

Uso: python music_long.py <music-cue.json> <saida.flac>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import soundfile as sf

import dsp
import music
from dsp import SR, n_samples

XF = 1.5  # crossfade entre blocos (s)


def sub_cue(cue: dict, a: float, b: float) -> dict:
    secs = []
    for s in cue["sections"]:
        if s["end"] <= a or s["start"] >= b:
            continue
        t = dict(s)
        t["start"] = round(max(0.0, s["start"] - a), 3)
        t["end"] = round(min(b, s["end"]) - a, 3)
        if s["start"] < a:
            t.pop("breath_before", None)
        secs.append(t)
    return {**cue, "length": round(b - a, 3), "grid_anchor": cue["grid_anchor"] - a, "sections": secs,
            "motifs": [{**m, "t": m["t"] - a} for m in cue.get("motifs", []) if a <= m["t"] < b],
            "toms": [t - a for t in cue.get("toms", []) if a <= t < b]}


def render_chunk(cue: dict) -> np.ndarray:
    stems = music.render(cue)
    g = music.GAINS
    mix = sum(stems[k] * g.get(k, 1.0) for k in stems if k != "fx")
    mix = mix * music.macro_envelope(cue, mix.shape[-1])
    mix = mix + stems["fx"] * g.get("fx", 1.0)
    mix = dsp.eq(mix, low_shelf=(60, 1.0), peaks=[(320, -1.5, 0.9), (2600, -2.0, 1.0)], high_shelf=(11000, 1.0))
    mix = dsp.compress(mix, -20, 2.0, 25, 250)
    return mix[:, : n_samples(cue["length"])]


def main(argv: list[str]) -> None:
    cue = json.loads(open(argv[1]).read())
    out = argv[2]
    L = cue["length"]
    # blocos terminando em trocas de seção, no máximo ~200 s cada
    bounds = [0.0]
    for s in cue["sections"]:
        if s["start"] - bounds[-1] >= 150 and s["start"] < L - 30:
            bounds.append(s["start"])
    bounds.append(L)
    total = np.zeros((2, n_samples(L)))
    for i in range(len(bounds) - 1):
        a = max(0.0, bounds[i] - (XF if i else 0.0))
        b = min(L, bounds[i + 1] + (XF if i + 1 < len(bounds) - 1 else 0.0))
        y = render_chunk(sub_cue(cue, a, b))
        n = y.shape[1]
        w = np.ones(n)
        k = n_samples(XF)
        if i:  # entra com cosseno (potência constante)
            w[:k] = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
        if i + 1 < len(bounds) - 1:
            w[-k:] = np.cos(np.linspace(0, np.pi / 2, k)) ** 2
        s0 = n_samples(a)
        total[:, s0:s0 + n] += y[:, : total.shape[1] - s0] * w[: total.shape[1] - s0]
        print(f"bloco {i + 1}/{len(bounds) - 1}: {a:.1f}–{b:.1f}s", flush=True)
    total = dsp.fade(total, 0.02, 1.5)
    total = dsp.limit(total, -2.0, 120)
    total = total * dsp.db(cue.get("target_lufs", -18.0) - dsp.loudness_lufs(total))
    total = dsp.limit(total, -1.5, 100)
    sf.write(out, total.T.astype(np.float32), SR, format="FLAC", subtype="PCM_24")
    print(f"{out}: {L:.1f}s · {dsp.loudness_lufs(total):.1f} LUFS")


if __name__ == "__main__":
    main(sys.argv)
