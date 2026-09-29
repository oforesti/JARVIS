"""Trilha original do filme JARVIS — composta por código, sincronizada ao corte.

Uso: python music.py <cue-map.json> <saida-dir>

O cue map descreve a estrutura do filme em segundos. A música tem uma grade de
compasso (bpm) ancorada em `grid_anchor` (o primeiro tempo forte da revelação), e
cada seção liga/desliga camadas com uma energia de 0 a 1. Tudo é determinístico.

Harmonia: Ré menor (i–VI–III–VII com 9as e 7as maiores), motivo quartal
A–D–E–A que volta no final em Ré maior (terça de picardia) sobre o logo.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import dsp
from dsp import SR, n_samples, t_axis

# ------------------------------------------------------------------ harmonia
CHORDS = {
    "Dm9":    {"pad": [50, 57, 60, 64, 65], "bass": 38, "arp": [62, 69, 76, 69, 77, 69, 76, 69]},
    "Bbmaj9": {"pad": [46, 57, 60, 62, 65], "bass": 34, "arp": [62, 69, 74, 69, 77, 69, 74, 69]},
    "Fmaj9":  {"pad": [53, 57, 60, 64, 67], "bass": 41, "arp": [60, 67, 72, 67, 76, 67, 72, 67]},
    "Cadd9":  {"pad": [52, 55, 60, 62, 67], "bass": 36, "arp": [60, 67, 74, 67, 76, 67, 74, 67]},
    "Dmaj9":  {"pad": [50, 57, 61, 64, 66], "bass": 38, "arp": [62, 69, 76, 69, 78, 69, 76, 69]},
    "Gmaj7":  {"pad": [43, 54, 59, 62, 66], "bass": 43, "arp": [62, 66, 71, 66, 74, 66, 71, 66]},
}
PROG = ["Dm9", "Bbmaj9", "Fmaj9", "Cadd9"]
MOTIF = [(69, 0.0, 0.5), (74, 0.5, 0.5), (76, 1.0, 1.0), (81, 2.0, 2.0)]  # (midi, beat, beats)


@dataclass
class Grid:
    bpm: float
    anchor: float

    @property
    def beat(self) -> float:
        return 60.0 / self.bpm

    @property
    def bar(self) -> float:
        return 4 * self.beat

    def bar_start(self, n: int) -> float:
        return self.anchor + n * self.bar

    def bars_between(self, t0: float, t1: float):
        n0 = int(np.ceil((t0 - self.anchor) / self.bar - 1e-6))
        n = n0
        while self.bar_start(n) < t1 - 1e-6:
            yield n, self.bar_start(n)
            n += 1


# --------------------------------------------------------------- instrumentos
def voice_pluck(m: float, L: float, bright: float, seed: int) -> np.ndarray:
    f = dsp.midi_hz(m)
    x = dsp.saw(f * 1.003, L, 0.1) * 0.5 + dsp.square(f * 0.997, L, 0.3, 0.42) * 0.35 + dsp.sine(f / 2, L) * 0.25
    t = t_axis(L)
    cut = 300 + (1200 + 5200 * bright) * np.exp(-t / (0.06 + 0.12 * bright))
    x = dsp.svf(x, cut, 1.1, "lp")
    return x * dsp.exp_decay(L, 0.18 + 0.25 * bright, 0.003)


def voice_bell(m: float, L: float) -> np.ndarray:
    f = dsp.midi_hz(m)
    t = t_axis(L)
    idx = 2.2 * np.exp(-t / 0.25)
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.01 * t))
    x += 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.5)
    return dsp.fade(x * dsp.exp_decay(L, 1.1, 0.004), 0, 0.3)


def voice_pad(notes, L: float, seed: int, bright: float = 0.5, soft: bool = False) -> np.ndarray:
    out = np.zeros(n_samples(L))
    for k, m in enumerate(notes):
        for j, det in enumerate((-0.09, -0.03, 0.04, 0.1) if not soft else (-0.05, 0.05)):
            f = dsp.midi_hz(m + det)
            ph = ((seed * 7 + k * 13 + j * 5) % 97) / 97
            if soft:
                out += dsp.triangle(f, L, ph) * 0.6 + dsp.sine(f, L, ph) * 0.4
            else:
                out += dsp.saw(f, L, ph)
    out /= len(notes) * (2 if soft else 4)
    t = t_axis(L)
    cut = 350 + 2600 * bright * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t + seed))
    return dsp.svf(out, cut, 0.8, "lp")


def voice_bass(m: float, L: float, drive: float = 1.4) -> np.ndarray:
    f = dsp.midi_hz(m)
    sub = dsp.sine(f, L)
    body = dsp.svf(dsp.saw(f, L, 0.25), 420, 0.9, "lp") * 0.55
    x = dsp.saturate(sub * 0.9 + body, drive)
    env = dsp.env_points([(0, 0), (0.008, 1), (L * 0.55, 0.85), (L, 0)], L, 2.0)
    return x * env


def drum_kick(L: float = 0.5) -> np.ndarray:
    t = t_axis(L)
    f = 44 + 120 * np.exp(-t / 0.035)
    x = dsp.sine(f, L) * dsp.exp_decay(L, 0.16, 0.001)
    click = dsp.svf(dsp.noise(L, 5), 3000, 0.7, "hp") * dsp.exp_decay(L, 0.004, 0.0002) * 0.6
    return dsp.saturate(x + click, 1.8)


def drum_snare(seed: int, L: float = 0.6) -> np.ndarray:
    t = t_axis(L)
    tone = dsp.sine(185 * (1 + 0.4 * np.exp(-t / 0.02)), L) * dsp.exp_decay(L, 0.07, 0.001) * 0.6
    nz = dsp.svf(dsp.noise(L, seed), 1800, 0.8, "bp") * dsp.exp_decay(L, 0.14, 0.001) * 1.4
    clap = np.zeros_like(t)
    for k, d in enumerate((0.0, 0.011, 0.023)):
        i = n_samples(d)
        seg = dsp.svf(dsp.noise(L, seed + 10 + k), 1400, 1.2, "bp") * dsp.exp_decay(L, 0.02, 0.0005)
        clap[i:] += seg[: len(t) - i] * 0.8
    return tone + nz * 0.7 + clap * 0.6


def drum_hat(seed: int, L: float = 0.09, open_: bool = False) -> np.ndarray:
    nz = dsp.noise(L if not open_ else 0.35, seed)
    x = dsp.svf(nz, 8500, 0.9, "hp") + dsp.svf(nz, 11000, 3.0, "bp") * 0.5
    Ls = L if not open_ else 0.35
    return x * dsp.exp_decay(Ls, 0.018 if not open_ else 0.12, 0.0005)


def drum_tick(seed: int) -> np.ndarray:
    L = 0.03
    x = dsp.svf(dsp.noise(L, seed), 6500, 5.0, "bp") * dsp.exp_decay(L, 0.003, 0.0002)
    return x + dsp.sine(3200, L) * dsp.exp_decay(L, 0.002, 0.0002) * 0.3


def tom(seed: int, m: float = 40, L: float = 1.2) -> np.ndarray:
    t = t_axis(L)
    f = dsp.midi_hz(m) * (1 + 0.6 * np.exp(-t / 0.05))
    x = dsp.sine(f, L) * dsp.exp_decay(L, 0.35, 0.002)
    x += dsp.svf(dsp.noise(L, seed), 700, 1.0, "lp") * dsp.exp_decay(L, 0.06, 0.001) * 0.6
    return dsp.saturate(x, 1.5)


# ------------------------------------------------------------------- arranjo
def energy_at(sections, t: float) -> float:
    for s in sections:
        if s["start"] <= t < s["end"]:
            return s.get("energy", 0.5)
    return 0.0


def section_at(sections, t: float):
    for s in sections:
        if s["start"] <= t < s["end"]:
            return s
    return None


def has(sec, layer: str) -> bool:
    return sec is not None and layer in sec.get("layers", [])


def render(cue: dict) -> dict[str, np.ndarray]:
    length = cue["length"]
    grid = Grid(cue["bpm"], cue["grid_anchor"])
    secs = cue["sections"]
    N = n_samples(length + 6.0)
    stems = {k: np.zeros((2, N)) for k in ("pad", "air", "bass", "arp", "drums", "motif", "fx")}

    # --- camada contínua: drone + ar (intro/respirações/final)
    for s in secs:
        if not ({"drone", "air"} & set(s.get("layers", []))):
            continue
        L = s["end"] - s["start"] + 2.5
        root = CHORDS[s.get("chord", "Dm9")]["bass"] - 12
        if "drone" in s["layers"]:
            d = dsp.sine(dsp.midi_hz(root + 12), L) * 0.5 + dsp.sine(dsp.midi_hz(root + 24), L) * 0.18
            d *= dsp.env_points([(0, 0), (min(2.5, L / 3), 1), (L - 2.5, 1), (L, 0)], L, 1.5)
            dsp.mix_at(stems["pad"], dsp.stereo(d) * 0.55, s["start"])
        if "air" in s["layers"]:
            chord = CHORDS[s.get("chord", "Dm9")]["pad"]
            a = voice_pad([m + 12 for m in chord[1:]], L, seed=int(s["start"] * 10), bright=0.35, soft=True)
            a = dsp.svf(dsp.pink(L, int(s["start"] * 10) + 1), 3200, 0.9, "bp") * 0.12 + a
            a *= dsp.env_points([(0, 0), (min(3.0, L / 2), 1), (L - 2.5, 1), (L, 0)], L, 1.5)
            dsp.mix_at(stems["air"], dsp.width(dsp.stereo(a), 1.6) * 0.8, s["start"])

    # --- compasso a compasso
    bar_i = 0
    for n, t_bar in grid.bars_between(0, length):
        s = section_at(secs, t_bar + 0.01)
        if s is None:
            continue
        e = s.get("energy", 0.5)
        prog = s.get("prog", PROG)
        cname = prog[(n - s.get("prog_offset", 0)) % len(prog)] if "chord" not in s else s["chord"]
        ch = CHORDS[cname]
        bar = grid.bar
        seed = 1000 + n
        # pad (supersaw macio)
        if has(s, "pad"):
            L = bar + 0.6
            p = voice_pad(ch["pad"], L, seed, bright=0.25 + 0.6 * e)
            p *= dsp.env_points([(0, 0), (0.25, 1), (bar - 0.05, 0.9), (L, 0)], L, 1.2)
            dsp.mix_at(stems["pad"], dsp.width(dsp.chorus(p, 0.35, 0.3, 0.5), 1.5) * (0.35 + 0.35 * e), t_bar)
        # baixo em colcheias com articulação
        if has(s, "bass"):
            pattern = s.get("bass_pattern", "eighths")
            steps = [0, 2, 3, 4, 6, 7] if pattern == "eighths" else [0, 8]
            for st in steps:
                L = grid.beat * (0.5 if pattern == "eighths" else 1.8) * 0.92
                b = voice_bass(ch["bass"] + (12 if st in (3, 7) and pattern == "eighths" else 0), L)
                acc = 1.0 if st in (0, 4) else 0.72
                dsp.mix_at(stems["bass"], dsp.stereo(b) * acc * (0.5 + 0.3 * e), t_bar + st * grid.beat / 2)
        # arpejo em semicolcheias
        if has(s, "arp"):
            for k in range(16):
                m = ch["arp"][k % 8] + (12 if (e > 0.8 and k % 4 == 3) else 0)
                L = grid.beat / 4 * 1.8
                br = min(1.0, 0.15 + 0.85 * e) * (1.0 if k % 4 == 0 else 0.75)
                v = voice_pluck(m, L, br, seed + k)
                pan_ = -0.35 + 0.7 * ((k * 5) % 8) / 7
                vel = (1.0 if k % 4 == 0 else 0.62 if k % 2 == 0 else 0.48) * (0.35 + 0.4 * e)
                dsp.mix_at(stems["arp"], dsp.pan(v, pan_) * vel, t_bar + k * grid.beat / 4)
        # bateria
        if has(s, "drums"):
            kit = s.get("kit", "half")
            kicks = {"pulse": [0, 8], "half": [0, 7, 10], "full": [0, 4, 8, 12]}[kit]
            for st in kicks:
                dsp.mix_at(stems["drums"], dsp.stereo(drum_kick()) * (0.95 if st == 0 else 0.7), t_bar + st * grid.beat / 4)
            if kit in ("half", "full"):
                dsp.mix_at(stems["drums"], dsp.stereo(drum_snare(seed)) * 0.55, t_bar + 8 * grid.beat / 4)
            for st in range(16):
                if st % 2 == 0 and kit == "pulse":
                    continue
                g = 0.18 if st % 4 == 2 else 0.1
                dsp.mix_at(stems["drums"], dsp.pan(drum_hat(seed + st), 0.25), t_bar + st * grid.beat / 4, g * (0.6 + 0.6 * e))
        if has(s, "ticks"):
            for st in range(16):
                dsp.mix_at(stems["drums"], dsp.pan(drum_tick(seed + st), -0.3 if st % 2 else 0.3),
                           t_bar + st * grid.beat / 4, 0.05 + 0.05 * (st % 4 == 0))
        bar_i += 1

    # --- motivo (sino) nos pontos marcados
    for mt in cue.get("motifs", []):
        t0 = mt["t"]
        transpose = mt.get("transpose", 0)
        for (m, b, dur) in MOTIF:
            L = max(1.5, dur * grid.beat + 1.2)
            v = voice_bell(m + transpose, L)
            if mt.get("pluck"):
                v = v * 0.6 + voice_pluck(m + transpose, L, 0.7, 7) * 0.5
            dsp.mix_at(stems["motif"], dsp.pan(v, 0.15 * np.sign(b - 1)), t0 + b * grid.beat, mt.get("gain", 0.5))

    # --- acentos: tons de impacto em inícios de seção marcados
    for h in cue.get("toms", []):
        dsp.mix_at(stems["fx"], dsp.stereo(tom(int(h * 10))) * 0.6, h)

    # --- sidechain (kick → baixo/pad/arp) — respiração sutil
    kick_env = np.abs(stems["drums"]).max(axis=0)
    kick_env = np.convolve(kick_env, np.ones(n_samples(0.03)) / n_samples(0.03), mode="same")
    duck = 1 - 0.35 * np.clip(kick_env / (kick_env.max() + 1e-9), 0, 1)
    for k in ("bass", "pad", "arp"):
        stems[k] *= duck

    # --- espacialização e tratamento por stem
    stems["pad"] = dsp.convolve_reverb(dsp.eq(stems["pad"], low_shelf=(120, -3), high_shelf=(9000, -2)), wet=0.35, ir_seconds=4.5, seed=51)
    stems["air"] = dsp.convolve_reverb(stems["air"], wet=0.5, ir_seconds=5.0, seed=53)
    stems["arp"] = dsp.convolve_reverb(dsp.pingpong(dsp.hp(stems["arp"], 180), seconds=grid.beat * 0.75, feedback=0.38, mix=0.3, tail=3),
                                       wet=0.22, ir_seconds=3.0, seed=55)
    stems["motif"] = dsp.convolve_reverb(dsp.pingpong(stems["motif"], seconds=grid.beat * 0.75, feedback=0.3, mix=0.22, tail=4),
                                         wet=0.45, ir_seconds=5.0, seed=57)
    stems["drums"] = dsp.convolve_reverb(dsp.compress(stems["drums"], -14, 3, 5, 90), wet=0.12, ir_seconds=2.0, seed=59)
    stems["fx"] = dsp.convolve_reverb(stems["fx"], wet=0.3, ir_seconds=3.5, seed=61)
    stems["bass"] = dsp.lp(stems["bass"], 1800)

    L = n_samples(length)
    for k in stems:
        stems[k] = dsp.pad_to(stems[k], L + n_samples(4))
    return stems


def macro_envelope(cue: dict, n: int) -> np.ndarray:
    """Arco dinâmico do filme: nível por seção (dB) + respirações antes das revelações."""
    t = np.arange(n) / SR
    pts = []
    for s in cue["sections"]:
        lvl = s.get("level_db", -18.0 * (1.0 - s.get("energy", 0.5)) ** 1.1)
        ramp = s.get("ramp", 1.2)
        pts.append((s["start"], lvl, ramp))
    env_db = np.full(n, pts[0][1])
    for i, (t0, lvl, ramp) in enumerate(pts):
        prev = pts[i - 1][1] if i else lvl
        k0 = n_samples(t0)
        k1 = min(n, k0 + n_samples(ramp))
        env_db[k0:] = lvl
        if k1 > k0:
            r = np.linspace(0, 1, k1 - k0)
            env_db[k0:k1] = prev + (lvl - prev) * (0.5 - 0.5 * np.cos(np.pi * r))
    env = 10 ** (env_db / 20)
    for s in cue["sections"]:
        b = s.get("breath_before", 0.0)
        if b <= 0:
            continue
        k_end = n_samples(s["start"])
        k_start = max(0, k_end - n_samples(b))
        k_fade = min(k_end, k_start + n_samples(min(0.18, b / 2)))
        fade_out = np.linspace(1, 0, max(1, k_fade - k_start)) ** 2
        env[k_start:k_fade] *= fade_out
        env[k_fade:k_end] = 0.0
        # retorno imediato no tempo forte (a revelação entra cheia)
    return env


def master(stems: dict[str, np.ndarray], gains: dict[str, float], length: float, cue: dict | None = None) -> np.ndarray:
    mix = sum(stems[k] * gains.get(k, 1.0) for k in stems if k != "fx")
    if cue is not None:
        mix = mix * macro_envelope(cue, mix.shape[-1])
    mix = mix + stems["fx"] * gains.get("fx", 1.0)
    mix = dsp.eq(mix, low_shelf=(60, 1.0), peaks=[(320, -1.5, 0.9), (2600, -2.0, 1.0)], high_shelf=(11000, 1.0))
    mix = dsp.compress(mix, -20, 2.0, 25, 250)
    mix = dsp.fade(mix[:, : n_samples(length)], 0.02, 1.5)
    mix = dsp.limit(mix, -2.0, 120)
    return mix


GAINS = {"pad": 0.9, "air": 0.7, "bass": 0.85, "arp": 0.55, "drums": 0.75, "motif": 0.6, "fx": 0.7}


def main(argv):
    cue = json.loads(Path(argv[1]).read_text())
    out = Path(argv[2])
    stems = render(cue)
    for k, v in stems.items():
        dsp.write(out / f"stem-{k}.wav", v[:, : n_samples(cue["length"])], peak_db=-1.0)
    mix = master(stems, {**GAINS, **cue.get("gains", {})}, cue["length"], cue)
    lufs = dsp.loudness_lufs(mix)
    target = cue.get("target_lufs", -18.0)
    mix = mix * dsp.db(target - lufs)
    mix = dsp.limit(mix, -1.5, 100)
    dsp.write(out / "music.wav", mix)
    print(f"music.wav  {cue['length']:.1f}s  LUFS {dsp.loudness_lufs(mix):.1f}  peak {20*np.log10(np.abs(mix).max()):.1f} dBFS")
    if "--png" in argv:
        dsp.spectrogram_png(mix, out / "music.png", "music")


if __name__ == "__main__":
    main(sys.argv)
