"""Biblioteca de sound design do filme JARVIS — gerada por síntese, 100% determinística.

Uso:  python sfx.py <pasta-de-saída> [--png <pasta-de-espectrogramas>]
Cada função devolve um sinal estéreo (2, n) em 48 kHz, normalizado depois por pico.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

import dsp
from dsp import SR, n_samples, t_axis


# ------------------------------------------------------------ blocos básicos
def _click(seed: int, bright: float = 4200, body: float = 380, length: float = 0.012) -> np.ndarray:
    r = dsp.rng(seed)
    n = dsp.noise(length, seed) * dsp.exp_decay(length, 0.0016, 0.0002)
    ping = dsp.svf(n, bright * r.uniform(0.92, 1.08), 6.0, "bp") * 2.2
    air = dsp.svf(n, 7000, 0.7, "hp") * 0.5
    tock = dsp.sine(body * r.uniform(0.95, 1.05), length) * dsp.exp_decay(length, 0.003, 0.0003) * 0.5
    return ping + air + tock


def ui_click(seed: int, soft: bool = False) -> np.ndarray:
    x = _click(seed, bright=3200 if soft else 4600, body=320 if soft else 420)
    x = dsp.pad_to(x, n_samples(0.12))
    x = dsp.stereo(x)
    x = dsp.convolve_reverb(x, wet=0.05, ir_seconds=0.6, seed=11, t60_low=0.35, t60_mid=0.3, t60_high=0.18)
    return dsp.fade(x[:, : n_samples(0.25)], 0, 0.05)


def tick(seed: int) -> np.ndarray:
    x = _click(seed, bright=6800, body=900, length=0.006) * 0.7
    return dsp.stereo(dsp.pad_to(x, n_samples(0.04)))


def pulse_digital(seed: int, base: float = 1320.0) -> np.ndarray:
    """Blip digital com FM decrescente e eco curto — 'o sistema respondeu'."""
    L = 0.09
    t = t_axis(L)
    idx = 3.0 * np.exp(-t / 0.018)
    mod = np.sin(2 * np.pi * base * 2.0 * t) * idx
    car = np.sin(2 * np.pi * base * t + mod)
    x = car * dsp.exp_decay(L, 0.022, 0.0015)
    x = dsp.pad_to(x, n_samples(0.5))
    x = dsp.pingpong(x, seconds=0.085, feedback=0.32, mix=0.28, tail=0.2)
    return dsp.fade(x, 0, 0.06)


def data_stream(seed: int, seconds: float = 1.2, density: float = 38.0) -> np.ndarray:
    """Chuva de micro-blips em escala pentatônica: dados em trânsito."""
    r = dsp.rng(seed)
    out = np.zeros((2, n_samples(seconds + 0.3)))
    scale = [0, 2, 4, 7, 9]
    count = int(seconds * density)
    times = np.sort(r.uniform(0, seconds, count))
    for i, at in enumerate(times):
        deg = scale[r.integers(0, 5)] + 12 * r.integers(0, 2)
        f = dsp.midi_hz(84 + deg)
        L = r.uniform(0.008, 0.02)
        b = dsp.sine(f, L) * dsp.exp_decay(L, L / 3, 0.0005)
        g = r.uniform(0.25, 0.8) * (0.55 + 0.45 * np.sin(np.pi * at / seconds))
        dsp.mix_at(out, dsp.pan(b, r.uniform(-0.8, 0.8)), at, g)
    bed = dsp.svf(dsp.noise(seconds + 0.3, seed + 1), 6500, 0.8, "hp") * 0.05
    bed *= dsp.env_points([(0, 0), (0.15, 1), (seconds - 0.2, 1), (seconds + 0.3, 0)], seconds + 0.3)
    out += dsp.stereo(bed)
    out = dsp.convolve_reverb(out, wet=0.12, ir_seconds=1.2, seed=13, t60_low=0.8, t60_mid=0.7, t60_high=0.4)
    return dsp.fade(out, 0.01, 0.2)


def whoosh(seed: int, seconds: float = 0.7, direction: int = 1, brightness: float = 1.0) -> np.ndarray:
    """Whoosh macio: ruído rosa com banda que sobe e desce, pan em movimento."""
    r = dsp.rng(seed)
    n = dsp.pink(seconds, seed)
    t = t_axis(seconds)
    peak = r.uniform(0.45, 0.6)
    env = np.exp(-((t / seconds - peak) ** 2) / (2 * 0.16 ** 2))
    fc = 350 + 2600 * brightness * env ** 1.5
    body = dsp.svf(n, fc, 1.4, "bp") * 1.6
    air = dsp.svf(n, 5200 * brightness, 0.8, "hp") * env * 0.25
    x = (body * env + air)
    p = direction * np.linspace(-0.7, 0.7, len(x))
    x = dsp.pan(x, p)
    x = dsp.convolve_reverb(x, wet=0.18, ir_seconds=1.6, seed=17, t60_low=1.0, t60_mid=0.9, t60_high=0.5)
    return dsp.fade(x, 0.02, 0.25)


def sweep(seed: int, seconds: float = 0.8, up: bool = True) -> np.ndarray:
    """Sweep de transição com ressonância — filtro abrindo (up) ou fechando."""
    n = dsp.noise(seconds, seed) + dsp.saw(55, seconds) * 0.08
    r = np.linspace(0, 1, n_samples(seconds))
    curve = r ** 2.2 if up else (1 - r) ** 1.6
    fc = 180 + 7800 * curve
    x = dsp.svf(n, fc, 5.0, "lp") * 0.9
    env = np.sin(np.pi * np.clip(r, 0, 1)) ** (0.6 if up else 1.2)
    if up:
        env = r ** 1.3
    x = x * env
    x = dsp.width(dsp.stereo(x) + dsp.pan(dsp.svf(n, fc * 1.5, 3, "bp") * 0.3 * env, 0.5), 1.3)
    x = dsp.convolve_reverb(x, wet=0.2, ir_seconds=1.8, seed=19)
    return dsp.fade(x, 0.01, 0.3)


def scan(seed: int, seconds: float = 1.1) -> np.ndarray:
    """Varredura: senoide que sobe com trêmolo rápido, atravessando L→R."""
    t = t_axis(seconds)
    f = 1400 * (5.2 ** (t / seconds))
    tone = dsp.sine(f, seconds) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 34 * t)))
    tone = dsp.svf(tone, 6000, 0.7, "lp")
    env = np.sin(np.pi * t / seconds) ** 0.8
    x = dsp.pan(tone * env * 0.5, np.linspace(-0.85, 0.85, len(t)))
    fizz = dsp.svf(dsp.noise(seconds, seed), 8000, 0.7, "hp") * env * 0.12
    x = x + dsp.stereo(fizz)
    x = dsp.convolve_reverb(x, wet=0.14, ir_seconds=1.2, seed=23, t60_low=0.9, t60_mid=0.8, t60_high=0.5)
    return dsp.fade(x, 0.02, 0.2)


def confirm(seed: int, notes=(81, 88), gap: float = 0.085) -> np.ndarray:
    """Confirmação de interface: duas notas de sino FM (A5 → E6)."""
    out = np.zeros((2, n_samples(1.6)))
    for k, m in enumerate(notes):
        L = 1.1
        t = t_axis(L)
        f = dsp.midi_hz(m)
        idx = 1.6 * np.exp(-t / 0.12)
        bell = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.5 * t))
        bell *= dsp.exp_decay(L, 0.28, 0.002)
        bell = dsp.fade(bell, 0, 0.45)
        dsp.mix_at(out, dsp.pan(bell, -0.25 + 0.5 * k), k * gap, 0.6)
    out = dsp.convolve_reverb(out, wet=0.28, ir_seconds=2.4, seed=29)
    return dsp.fade(out, 0, 0.4)


def hit_sub(seed: int, weight: float = 1.0, tail: float = 3.2) -> np.ndarray:
    """Impacto cinematográfico grave: queda de pitch + corpo + transiente + cauda."""
    r = dsp.rng(seed)
    L = 2.4
    t = t_axis(L)
    f = 38 + 95 * np.exp(-t / 0.07)
    boom = dsp.sine(f, L) * dsp.exp_decay(L, 0.55 * weight, 0.003)
    boom = dsp.saturate(boom * 1.2, 1.6)
    body_n = dsp.noise(L, seed)
    body = dsp.svf(body_n, 160 + 900 * np.exp(-t / 0.05), 0.9, "lp") * dsp.exp_decay(L, 0.09, 0.001) * 2.2
    crack = dsp.svf(dsp.noise(L, seed + 3), 3500, 0.7, "hp") * dsp.exp_decay(L, 0.012, 0.0003) * 0.9
    x = boom * 0.95 + body * 0.55 + crack * 0.35 * r.uniform(0.8, 1.1)
    x = dsp.fade(dsp.stereo(x), 0, 0.7)
    x = dsp.convolve_reverb(x, wet=0.35, ir_seconds=tail, seed=31, tone_hp=90, tone_lp=5000,
                            t60_low=3.6, t60_mid=2.4, t60_high=0.9)
    x = dsp.eq(x, low_shelf=(80, 2.0), peaks=[(300, -3.0, 0.8)])
    return dsp.fade(x, 0, 0.8)


def sub_drop(seed: int, seconds: float = 2.2) -> np.ndarray:
    t = t_axis(seconds)
    f = 30 + 34 * np.exp(-t / 0.5)
    s = dsp.sine(f, seconds) * dsp.env_points([(0, 0), (0.012, 1), (seconds, 0)], seconds, curve=3.0)
    harm = np.tanh(s * 2.4) * 0.35  # 2º/3º harmônicos: audível em alto-falante pequeno
    x = dsp.stereo(s * 0.8 + harm)
    return dsp.fade(x, 0, 0.4)


def riser(seed: int, seconds: float = 2.6) -> np.ndarray:
    """Riser: ruído em banda subindo + acorde de serras em glissando + trêmolo acelerando."""
    t = t_axis(seconds)
    r = t / seconds
    amp = r ** 2.4
    nz = dsp.noise(seconds, seed)
    fc = 300 * (22 ** (r ** 1.3))
    q = 1.2 + 4.0 * r
    band = dsp.svf(nz, fc, q, "bp") * 1.4
    chord = np.zeros_like(t)
    for k, (m, det) in enumerate([(50, -0.07), (57, 0.05), (62, -0.03), (69, 0.08), (74, 0.0)]):
        f = dsp.midi_hz(m + det) * (2 ** (r * 1.0))
        chord += dsp.saw(f, seconds, phase=k * 0.21)
    chord = dsp.svf(chord / 5, 400 + 7000 * r ** 1.8, 1.2, "lp")
    trem_rate = 6 + 22 * r ** 1.5
    trem = 0.72 + 0.28 * np.sin(2 * np.pi * np.cumsum(trem_rate) / SR)
    x = (band * 0.8 + chord * 0.55) * amp * trem
    x = dsp.width(dsp.stereo(x) + dsp.pan(dsp.svf(nz, fc * 1.6, 2, "bp") * amp * 0.4, -0.4), 1.4)
    x = dsp.convolve_reverb(x, wet=0.22, ir_seconds=2.0, seed=37)
    n_end = n_samples(seconds + 0.02)
    x = x[:, :n_end]
    return dsp.fade(x, 0.05, 0.015)


def reverse_impact(seed: int, seconds: float = 1.4) -> np.ndarray:
    """Swell reverso: cauda de impacto invertida que cresce até o corte."""
    h = hit_sub(seed, weight=0.8, tail=3.5)
    sh = dsp.convolve_reverb(dsp.svf(dsp.noise(0.3, seed + 5), 2500, 0.7, "hp")
                             * dsp.exp_decay(0.3, 0.04), wet=1.0, ir_seconds=3.0, seed=41)
    x = dsp.pad_to(h, max(h.shape[-1], sh.shape[-1])) + dsp.pad_to(sh, max(h.shape[-1], sh.shape[-1])) * 0.5
    x = x[:, ::-1]
    n = n_samples(seconds)
    x = x[:, -n:]
    return dsp.fade(x, 0.08, 0.004)


def swell_air(seed: int, seconds: float = 1.8) -> np.ndarray:
    """Respiração antes da revelação: ar filtrado em crescendo, sem tom."""
    t = t_axis(seconds)
    r = t / seconds
    nz = dsp.pink(seconds, seed)
    x = dsp.svf(nz, 2500 + 6000 * r, 0.8, "hp") * (r ** 2.8)
    x = dsp.width(dsp.stereo(x) + dsp.pan(dsp.svf(nz, 900 + 3000 * r, 2.0, "bp") * r ** 3 * 0.5, 0.3), 1.5)
    return dsp.fade(x, 0.1, 0.01)


def electric(seed: int, seconds: float = 3.0) -> np.ndarray:
    """Textura elétrica sutil: estalos esparsos + zumbido harmônico baixíssimo."""
    r = dsp.rng(seed)
    t = t_axis(seconds)
    hum = sum(np.sin(2 * np.pi * 60 * k * t + k) / k ** 1.3 for k in range(1, 9)) * 0.05
    hum = dsp.svf(hum, 900, 0.7, "lp")
    crackle = np.zeros_like(t)
    for _ in range(int(seconds * 22)):
        i = r.integers(0, len(t) - 200)
        crackle[i:i + 40] += r.uniform(-1, 1) * np.exp(-np.arange(40) / 6)
    crackle = dsp.svf(crackle, 3200, 0.9, "hp") * 0.5
    fizz = dsp.svf(dsp.noise(seconds, seed + 2), 9000, 0.7, "hp") * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)) * 0.05
    x = dsp.width(dsp.pan(hum, 0) + dsp.pan(crackle, np.sin(2 * np.pi * 0.3 * t) * 0.6) + dsp.stereo(fizz), 1.2)
    return dsp.fade(x, 0.3, 0.6)


def boot(seed: int, seconds: float = 2.4) -> np.ndarray:
    """Power-up do núcleo: zumbido que sobe + ignição + harmônicos abrindo."""
    t = t_axis(seconds)
    r = t / seconds
    f = 32 + 60 * r ** 1.6
    drone = dsp.saw(f, seconds) * 0.5 + dsp.sine(f, seconds)
    drone = dsp.svf(drone, 120 + 2400 * r ** 2, 1.1 + 2.5 * r, "lp")
    amp = np.minimum(1, r * 2.2) ** 1.5
    ign = dsp.svf(dsp.noise(seconds, seed), 5000, 0.7, "hp") * np.exp(-t / 0.05) * 0.4
    x = dsp.stereo(drone * amp * 0.7 + ign) + electric(seed + 1, seconds) * 0.4
    x = dsp.fade(x, 0, 0.45)
    x = dsp.convolve_reverb(x, wet=0.25, ir_seconds=2.4, seed=43)
    return dsp.fade(x, 0.02, 0.5)


def glitch(seed: int, seconds: float = 0.22) -> np.ndarray:
    """Glitch controlado: fragmentos de blip repetidos com bitcrush — usar no máximo 2×."""
    r = dsp.rng(seed)
    src = data_stream(seed + 7, 0.25, 90)[:, : n_samples(0.25)]
    out = np.zeros((2, n_samples(seconds + 0.05)))
    pos = 0.0
    while pos < seconds:
        L = r.choice([0.012, 0.018, 0.024, 0.036])
        a = r.integers(0, src.shape[-1] - n_samples(L))
        frag = src[:, a:a + n_samples(L)]
        dsp.mix_at(out, frag, pos, r.uniform(0.6, 1.2))
        pos += L * r.choice([1.0, 1.0, 0.5])
    steps = 2 ** 5
    out = np.round(out * steps) / steps
    out = dsp.svf(out, 7500, 0.9, "lp")
    return dsp.fade(out, 0.002, 0.03)


def lock_in(seed: int) -> np.ndarray:
    """Encaixe: dois cliques rápidos + um thump grave — elemento que trava no lugar."""
    out = np.zeros((2, n_samples(0.6)))
    dsp.mix_at(out, ui_click(seed), 0.0, 0.8)
    dsp.mix_at(out, ui_click(seed + 1), 0.045, 0.6)
    L = 0.3
    tt = t_axis(L)
    thump = dsp.sine(70 + 60 * np.exp(-tt / 0.02), L) * dsp.exp_decay(L, 0.07)
    dsp.mix_at(out, dsp.stereo(thump), 0.04, 0.7)
    return dsp.fade(out, 0, 0.1)


def signature(seed: int, seconds: float = 6.5) -> np.ndarray:
    """Assinatura sonora do logo: sub + acorde D6/9 etéreo + sino + shimmer."""
    t = t_axis(seconds)
    out = np.zeros((2, n_samples(seconds)))
    # sub em D
    sub = dsp.sine(dsp.midi_hz(26), seconds) * dsp.env_points([(0, 0), (0.08, 1), (2.5, 0.6), (seconds, 0)], seconds, 2.0)
    out += dsp.stereo(sub * 0.28)
    # acorde (D, A, E, F#, B) com vozes levemente desafinadas
    pad = np.zeros_like(t)
    for k, m in enumerate([50, 57, 64, 66, 71, 74]):
        for det in (-0.06, 0.0, 0.07):
            pad += dsp.saw(dsp.midi_hz(m + det), seconds, phase=0.13 * k + det)
    pad = dsp.svf(pad / 18, 500 + 1800 * dsp.env_points([(0, 0), (1.2, 1), (seconds, 0.3)], seconds), 0.8, "lp")
    pad *= dsp.env_points([(0, 0), (0.35, 1), (3.5, 0.7), (seconds, 0)], seconds, 2.0)
    out += dsp.width(dsp.chorus(pad * 0.5, rate=0.3, depth=0.3, mix=0.5)[:, : out.shape[-1]], 1.5)
    # sino em D6 com FM
    L = 3.5
    tb = t_axis(L)
    f = dsp.midi_hz(86)
    bell = np.sin(2 * np.pi * f * tb + 1.4 * np.exp(-tb / 0.3) * np.sin(2 * np.pi * f * 2.76 * tb))
    bell *= dsp.exp_decay(L, 0.9, 0.003)
    bell = dsp.fade(bell, 0, 0.8)
    dsp.mix_at(out, dsp.pan(bell, 0.1), 0.02, 0.34)
    # centelhas digitais no ataque
    sp = data_stream(seed + 3, 0.5, 30)
    dsp.mix_at(out, sp, 0.0, 0.35)
    out = dsp.convolve_reverb(out, wet=0.45, ir_seconds=5.0, seed=47, t60_low=4.5, t60_mid=3.8, t60_high=1.8)
    return dsp.fade(out[:, : n_samples(seconds + 2.5)], 0.0, 1.6)


LIBRARY = {
    "ui-click-1": lambda: ui_click(101),
    "ui-click-2": lambda: ui_click(102),
    "ui-click-3": lambda: ui_click(103, soft=True),
    "ui-click-soft": lambda: ui_click(104, soft=True),
    "tick": lambda: tick(105),
    "pulse-a": lambda: pulse_digital(201, 1320),
    "pulse-b": lambda: pulse_digital(202, 1760),
    "pulse-c": lambda: pulse_digital(203, 990),
    "data-stream-1": lambda: data_stream(301, 1.2),
    "data-stream-2": lambda: data_stream(302, 2.0, 30),
    "whoosh-soft-1": lambda: whoosh(401, 0.65, 1),
    "whoosh-soft-2": lambda: whoosh(402, 0.8, -1),
    "whoosh-soft-3": lambda: whoosh(403, 0.55, 1, 1.3),
    "whoosh-deep": lambda: whoosh(404, 1.1, 1, 0.55),
    "sweep-up": lambda: sweep(501, 0.9, True),
    "sweep-down": lambda: sweep(502, 0.8, False),
    "scan": lambda: scan(601),
    "confirm": lambda: confirm(701),
    "confirm-low": lambda: confirm(702, notes=(69, 76)),
    "hit-sub-1": lambda: hit_sub(801, 1.0),
    "hit-sub-2": lambda: hit_sub(802, 1.25),
    "hit-soft": lambda: hit_sub(803, 0.6, 2.2),
    "sub-drop": lambda: sub_drop(901),
    "riser-short": lambda: riser(1001, 1.5),
    "riser-long": lambda: riser(1002, 3.2),
    "reverse-impact": lambda: reverse_impact(1101),
    "swell-air": lambda: swell_air(1201),
    "electric": lambda: electric(1301),
    "boot": lambda: boot(1401),
    "glitch-1": lambda: glitch(1501),
    "glitch-2": lambda: glitch(1502, 0.3),
    "lock-in": lambda: lock_in(1601),
    "signature": lambda: signature(1701),
}

PEAKS = {  # nível de pico por família (dBFS) — mix final ajusta em cima disso
    "ui-click": -6, "tick": -12, "pulse": -8, "data-stream": -10, "whoosh": -6, "sweep": -7,
    "scan": -9, "confirm": -8, "hit": -1, "sub-drop": -2, "riser": -3, "reverse-impact": -3,
    "swell-air": -8, "electric": -14, "boot": -4, "glitch": -9, "lock-in": -5, "signature": -2,
}


def trim_tail(x: np.ndarray, floor_db: float = -72.0, keep: float = 0.05) -> np.ndarray:
    m = np.max(np.abs(dsp.stereo(x)), axis=0)
    thr = np.max(m) * dsp.db(floor_db)
    idx = np.nonzero(m > thr)[0]
    if len(idx) == 0:
        return x
    end = min(x.shape[-1], idx[-1] + n_samples(keep))
    return dsp.fade(x[..., :end], 0, keep)


def peak_for(name: str) -> float:
    for k, v in PEAKS.items():
        if name.startswith(k):
            return v
    return -3


def main(argv: list[str]) -> None:
    out = Path(argv[1])
    png = Path(argv[argv.index("--png") + 1]) if "--png" in argv else None
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
    for name, fn in LIBRARY.items():
        if only and name not in only:
            continue
        x = trim_tail(fn())
        path = dsp.write(out / f"{name}.flac", x, peak_db=peak_for(name))
        dur = x.shape[-1] / SR
        print(f"{name:18s} {dur:5.2f}s  -> {path.name}")
        if png:
            png.mkdir(parents=True, exist_ok=True)
            dsp.spectrogram_png(dsp.read(path), png / f"{name}.png", name)


if __name__ == "__main__":
    main(sys.argv)
