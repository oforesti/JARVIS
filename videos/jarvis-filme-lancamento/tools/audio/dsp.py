"""Núcleo de DSP para o sound design e a trilha do filme JARVIS.

Tudo é determinístico (RNG com semente), em 48 kHz, float64 internamente.
Sinais estéreo têm shape (2, n). Mono tem shape (n,).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import soundfile as sf
from numba import njit
from pedalboard import (Chorus, Compressor, Delay, Distortion, HighpassFilter,
                        HighShelfFilter, Limiter, LowpassFilter, LowShelfFilter,
                        Pedalboard, PeakFilter, Reverb)

SR = 48_000


# ----------------------------------------------------------------- utilidades
def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def n_samples(seconds: float) -> int:
    return int(round(seconds * SR))


def t_axis(seconds: float) -> np.ndarray:
    return np.arange(n_samples(seconds)) / SR


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def db(x: float) -> float:
    return 10 ** (x / 20)


def stereo(x: np.ndarray) -> np.ndarray:
    return x if x.ndim == 2 else np.vstack([x, x])


def pan(x: np.ndarray, p: float | np.ndarray) -> np.ndarray:
    """Equal-power pan. p em [-1, 1] (pode ser array por amostra)."""
    m = x if x.ndim == 1 else x.mean(axis=0)
    ang = (np.asarray(p) + 1) * math.pi / 4
    return np.vstack([m * np.cos(ang), m * np.sin(ang)])


def width(x: np.ndarray, w: float) -> np.ndarray:
    x = stereo(x)
    mid = (x[0] + x[1]) / 2
    side = (x[0] - x[1]) / 2 * w
    return np.vstack([mid + side, mid - side])


def pad_to(x: np.ndarray, n: int) -> np.ndarray:
    if x.shape[-1] >= n:
        return x[..., :n]
    pad = [(0, 0)] * (x.ndim - 1) + [(0, n - x.shape[-1])]
    return np.pad(x, pad)


def mix_at(dst: np.ndarray, src: np.ndarray, at_s: float, gain: float = 1.0) -> None:
    """Soma src em dst a partir de at_s segundos (in place)."""
    src = stereo(src) if dst.ndim == 2 else src
    i = n_samples(at_s)
    if i >= dst.shape[-1]:
        return
    j = min(dst.shape[-1], i + src.shape[-1])
    dst[..., i:j] += src[..., : j - i] * gain


def fade(x: np.ndarray, fin: float = 0.0, fout: float = 0.0, curve: str = "cos") -> np.ndarray:
    y = x.copy()
    n = y.shape[-1]
    for length, rising in ((fin, True), (fout, False)):
        k = min(n, n_samples(length))
        if k <= 1:
            continue
        r = np.linspace(0, 1, k)
        e = (0.5 - 0.5 * np.cos(np.pi * r)) if curve == "cos" else r
        if rising:
            y[..., :k] *= e
        else:
            y[..., n - k:] *= e[::-1]
    return y


def normalize_peak(x: np.ndarray, peak_db: float = -1.0) -> np.ndarray:
    p = np.max(np.abs(x))
    return x if p == 0 else x * (db(peak_db) / p)


def write(path: str | Path, x: np.ndarray, peak_db: float | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    y = stereo(x)
    if peak_db is not None:
        y = normalize_peak(y, peak_db)
    y = np.clip(y, -1.0, 1.0)
    fmt = "FLAC" if path.suffix.lower() == ".flac" else "WAV"
    sf.write(str(path), y.T.astype(np.float32), SR, format=fmt, subtype="PCM_24")
    return path


def read(path: str | Path) -> np.ndarray:
    y, sr = sf.read(str(path), always_2d=True)
    if sr != SR:
        raise ValueError(f"{path}: {sr} Hz (esperado {SR})")
    return y.T.astype(np.float64)


# -------------------------------------------------------------- osciladores
def sine(freq, seconds: float, phase: float = 0.0) -> np.ndarray:
    n = n_samples(seconds)
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    ph = phase + 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph)


@njit(cache=True)
def _polyblep(t: float, dt: float) -> float:
    if t < dt:
        t /= dt
        return t + t - t * t - 1.0
    if t > 1.0 - dt:
        t = (t - 1.0) / dt
        return t * t + t + t + 1.0
    return 0.0


@njit(cache=True)
def _saw(freq: np.ndarray, phase0: float) -> np.ndarray:
    out = np.empty(freq.shape[0])
    ph = phase0
    for i in range(freq.shape[0]):
        dt = freq[i] / 48000.0
        out[i] = 2.0 * ph - 1.0 - _polyblep(ph, dt)
        ph += dt
        if ph >= 1.0:
            ph -= 1.0
    return out


@njit(cache=True)
def _square(freq: np.ndarray, phase0: float, pw: float) -> np.ndarray:
    out = np.empty(freq.shape[0])
    ph = phase0
    for i in range(freq.shape[0]):
        dt = freq[i] / 48000.0
        v = 1.0 if ph < pw else -1.0
        v += _polyblep(ph, dt)
        t2 = ph - pw
        if t2 < 0.0:
            t2 += 1.0
        v -= _polyblep(t2, dt)
        out[i] = v
        ph += dt
        if ph >= 1.0:
            ph -= 1.0
    return out


def saw(freq, seconds: float, phase: float = 0.0) -> np.ndarray:
    n = n_samples(seconds)
    f = np.ascontiguousarray(np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,)))
    return _saw(f, phase % 1.0)


def square(freq, seconds: float, phase: float = 0.0, pw: float = 0.5) -> np.ndarray:
    n = n_samples(seconds)
    f = np.ascontiguousarray(np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,)))
    return _square(f, phase % 1.0, pw)


def triangle(freq, seconds: float, phase: float = 0.0) -> np.ndarray:
    # integração de quadrada band-limited (leaky) -> triângulo suave
    sq = square(freq, seconds, phase)
    n = len(sq)
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    tri = np.cumsum(sq * 4 * f / SR)
    tri -= np.convolve(tri, np.ones(2048) / 2048, mode="same")
    return tri / (np.max(np.abs(tri)) + 1e-12)


def noise(seconds: float, seed: int) -> np.ndarray:
    return rng(seed).standard_normal(n_samples(seconds)) * 0.3


def pink(seconds: float, seed: int) -> np.ndarray:
    n = n_samples(seconds)
    w = rng(seed).standard_normal(n)
    spec = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    spec /= np.sqrt(f)
    y = np.fft.irfft(spec, n)
    return y / (np.std(y) + 1e-12) * 0.3


# ---------------------------------------------------------------- envelopes
def env_points(points: list[tuple[float, float]], seconds: float, curve: float = 0.0) -> np.ndarray:
    """Envelope por pontos (t, v). curve>0 = exponencial suave entre pontos."""
    n = n_samples(seconds)
    t = np.arange(n) / SR
    ts = np.array([p[0] for p in points], dtype=np.float64)
    vs = np.array([p[1] for p in points], dtype=np.float64)
    if curve == 0:
        return np.interp(t, ts, vs)
    out = np.empty(n)
    idx = np.clip(np.searchsorted(ts, t, side="right") - 1, 0, len(ts) - 2)
    t0, t1 = ts[idx], ts[idx + 1]
    v0, v1 = vs[idx], vs[idx + 1]
    r = np.clip((t - t0) / np.maximum(t1 - t0, 1e-9), 0, 1)
    shaped = (np.exp(curve * r) - 1) / (np.exp(curve) - 1)
    out[:] = v0 + (v1 - v0) * np.where(v1 > v0, 1 - (np.exp(curve * (1 - r)) - 1) / (np.exp(curve) - 1), shaped)
    out[t >= ts[-1]] = vs[-1]
    return out


def adsr(seconds: float, a: float, d: float, s: float, r: float, hold: float | None = None) -> np.ndarray:
    n = n_samples(seconds)
    hold = seconds - r if hold is None else hold
    t = np.arange(n) / SR
    e = np.zeros(n)
    e = np.where(t < a, t / max(a, 1e-6), e)
    dec = (t >= a) & (t < a + d)
    e = np.where(dec, 1 - (1 - s) * (t - a) / max(d, 1e-6), e)
    e = np.where((t >= a + d) & (t < hold), s, e)
    rel = t >= hold
    level_at_hold = s if hold >= a + d else (hold / max(a, 1e-6) if hold < a else 1 - (1 - s) * (hold - a) / max(d, 1e-6))
    e = np.where(rel, level_at_hold * np.exp(-(t - hold) / max(r / 5, 1e-6)), e)
    return e


def exp_decay(seconds: float, tau: float, attack: float = 0.002) -> np.ndarray:
    t = t_axis(seconds)
    return np.minimum(1.0, t / max(attack, 1e-6)) * np.exp(-t / tau)


# ------------------------------------------------------------------- filtros
@njit(cache=True)
def _svf(x: np.ndarray, cutoff: np.ndarray, q: np.ndarray, mode: int) -> np.ndarray:
    """Zavalishin TPT SVF. mode 0=LP 1=BP 2=HP 3=notch."""
    out = np.empty_like(x)
    ic1 = 0.0
    ic2 = 0.0
    for i in range(x.shape[0]):
        fc = min(max(cutoff[i], 10.0), 22000.0)
        g = math.tan(math.pi * fc / 48000.0)
        k = 1.0 / max(q[i], 0.05)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x[i] - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        if mode == 0:
            out[i] = v2
        elif mode == 1:
            out[i] = v1
        elif mode == 2:
            out[i] = x[i] - k * v1 - v2
        else:
            out[i] = x[i] - k * v1
    return out


def svf(x: np.ndarray, cutoff, q=0.707, mode: str = "lp") -> np.ndarray:
    modes = {"lp": 0, "bp": 1, "hp": 2, "notch": 3}
    if x.ndim == 2:
        return np.vstack([svf(ch, cutoff, q, mode) for ch in x])
    n = x.shape[0]
    c = np.ascontiguousarray(np.broadcast_to(np.asarray(cutoff, dtype=np.float64), (n,)))
    qq = np.ascontiguousarray(np.broadcast_to(np.asarray(q, dtype=np.float64), (n,)))
    return _svf(np.ascontiguousarray(x, dtype=np.float64), c, qq, modes[mode])


def board(x: np.ndarray, plugins: list) -> np.ndarray:
    y = stereo(x).astype(np.float32)
    out = Pedalboard(plugins)(y, SR)
    return out.astype(np.float64)


def hp(x, f):
    return board(x, [HighpassFilter(cutoff_frequency_hz=f)])


def lp(x, f):
    return board(x, [LowpassFilter(cutoff_frequency_hz=f)])


def eq(x, *, low_shelf=None, high_shelf=None, peaks=()):
    chain = []
    if low_shelf:
        chain.append(LowShelfFilter(cutoff_frequency_hz=low_shelf[0], gain_db=low_shelf[1], q=0.7))
    for f, g, q in peaks:
        chain.append(PeakFilter(cutoff_frequency_hz=f, gain_db=g, q=q))
    if high_shelf:
        chain.append(HighShelfFilter(cutoff_frequency_hz=high_shelf[0], gain_db=high_shelf[1], q=0.7))
    return board(x, chain) if chain else stereo(x)


def saturate(x: np.ndarray, drive: float = 2.0) -> np.ndarray:
    return np.tanh(x * drive) / np.tanh(drive)


def reverb(x, size=0.85, wet=0.3, dry=0.8, damping=0.5, width_=1.0, tail=3.0):
    y = pad_to(stereo(x), stereo(x).shape[-1] + n_samples(tail))
    return board(y, [Reverb(room_size=size, wet_level=wet, dry_level=dry, damping=damping, width=width_)])


def delay(x, seconds=0.25, feedback=0.3, mix=0.25, tail=1.5):
    y = pad_to(stereo(x), stereo(x).shape[-1] + n_samples(tail))
    return board(y, [Delay(delay_seconds=seconds, feedback=feedback, mix=mix)])


def pingpong(x, seconds=0.25, feedback=0.35, mix=0.25, tail=2.0):
    """Delay estéreo cruzado (L->R->L)."""
    x = pad_to(stereo(x), stereo(x).shape[-1] + n_samples(tail))
    d = n_samples(seconds)
    out = x.copy()
    tapL = np.zeros_like(x[0])
    tapR = np.zeros_like(x[1])
    src = x.mean(axis=0)
    g = mix
    shift = d
    side = 0
    while g > 1e-3 and shift < x.shape[-1]:
        tgt = tapL if side == 0 else tapR
        tgt[shift:] += src[:-shift] * g
        g *= feedback
        shift += d
        side ^= 1
    out[0] += tapL
    out[1] += tapR
    return out


def chorus(x, rate=0.6, depth=0.25, mix=0.35):
    return board(x, [Chorus(rate_hz=rate, depth=depth, centre_delay_ms=9.0, feedback=0.0, mix=mix)])


def compress(x, threshold=-18, ratio=3, attack=10, release=120):
    return board(x, [Compressor(threshold_db=threshold, ratio=ratio, attack_ms=attack, release_ms=release)])


@njit(cache=True)
def _limiter_gain(peak: np.ndarray, ceiling: float, look: int, rel_coef: float) -> np.ndarray:
    n = peak.shape[0]
    need = np.empty(n)
    for i in range(n):
        p = peak[i]
        need[i] = 1.0 if p <= ceiling else ceiling / p
    # mínimo deslizante à frente (lookahead) — o ganho já está baixo quando o pico chega
    ahead = np.empty(n)
    for i in range(n):
        m = 1.0
        j_end = min(n, i + look + 1)
        for j in range(i, j_end):
            if need[j] < m:
                m = need[j]
        ahead[i] = m
    g = np.empty(n)
    cur = 1.0
    for i in range(n):
        target = ahead[i]
        if target < cur:
            cur = target
        else:
            cur = target + (cur - target) * rel_coef
        g[i] = cur
    # suaviza o ataque com uma rampa curta (evita distorção de degrau)
    out = np.empty(n)
    acc = 0.0
    w = max(1, look // 2)
    for i in range(n):
        acc += g[i]
        if i >= w:
            acc -= g[i - w]
        out[i] = acc / min(i + 1, w)
    for i in range(n):
        if out[i] > g[i] and ahead[i] < 1.0:
            out[i] = min(out[i], ahead[i])
    return out


def limit(x, threshold=-1.0, release=80, lookahead_ms=5.0):
    """Limitador brickwall com lookahead e detecção de true peak (4× oversampling). Sem ganho oculto."""
    from scipy.signal import resample_poly
    x = stereo(x)
    up = np.abs(resample_poly(x, 4, 1, axis=1))
    peak4 = up.max(axis=0)
    peak = peak4.reshape(-1, 4).max(axis=1)[: x.shape[-1]]
    if peak.shape[0] < x.shape[-1]:
        peak = np.pad(peak, (0, x.shape[-1] - peak.shape[0]))
    look = max(1, int(lookahead_ms * SR / 1000))
    rel = math.exp(-1.0 / (release * SR / 1000))
    # offline: o mínimo à frente já antecipa o pico; nenhum atraso de sinal é necessário
    g = _limiter_gain(np.ascontiguousarray(peak), db(threshold), look, rel)
    return x * g


# ------------------------------------------------------- reverb de convolução
def hall_ir(seconds: float = 4.0, seed: int = 7, predelay: float = 0.018,
            t60_low: float = 3.2, t60_mid: float = 2.6, t60_high: float = 1.2) -> np.ndarray:
    """IR estéreo sintético com decaimento dependente da frequência."""
    n = n_samples(seconds)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        w = rng(seed + ch).standard_normal(n)
        low = svf(w, 350, 0.6, "lp")
        high = svf(w, 3500, 0.6, "hp")
        mid = w - low - high
        k = 6.91  # ln(1000)
        y = (low * np.exp(-k * t / t60_low) + mid * np.exp(-k * t / t60_mid)
             + high * np.exp(-k * t / t60_high))
        # early reflections esparsas
        er = np.zeros(n)
        r = rng(seed + 10 + ch)
        for _ in range(28):
            i = int(r.uniform(0.004, 0.09) * SR)
            er[i] += r.uniform(-1, 1) * 0.9
        y = y * 0.12 + er * np.exp(-t / 0.05)
        y = np.concatenate([np.zeros(n_samples(predelay)), y])[:n]
        out.append(y)
    ir = np.vstack(out)
    ir /= np.sqrt(np.sum(ir ** 2) / 2)
    return ir


_IR_CACHE: dict = {}


def convolve_reverb(x: np.ndarray, wet: float = 0.25, ir_seconds: float = 4.0, seed: int = 7,
                    tone_hp: float = 180, tone_lp: float = 9000, **ir_kw) -> np.ndarray:
    from scipy.signal import fftconvolve
    key = (ir_seconds, seed, tuple(sorted(ir_kw.items())))
    if key not in _IR_CACHE:
        _IR_CACHE[key] = hall_ir(ir_seconds, seed, **ir_kw)
    ir = _IR_CACHE[key]
    x = stereo(x)
    send = lp(hp(x, tone_hp), tone_lp)
    wetL = fftconvolve(send[0], ir[0])
    wetR = fftconvolve(send[1], ir[1])
    wet_sig = np.vstack([wetL, wetR])
    out = pad_to(x, wet_sig.shape[-1])
    return out + wet_sig * wet


# ------------------------------------------------------------- análise simples
def loudness_lufs(x: np.ndarray) -> float:
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    return float(meter.integrated_loudness(stereo(x).T))


def spectrogram_png(x: np.ndarray, path: str | Path, title: str = "") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    m = stereo(x).mean(axis=0)
    fig, ax = plt.subplots(2, 1, figsize=(10, 5), sharex=True, gridspec_kw={"height_ratios": [1, 2]})
    t = np.arange(len(m)) / SR
    ax[0].plot(t, m, lw=0.4, color="#5cd6f5")
    ax[0].set_ylim(-1, 1)
    ax[0].set_title(title)
    ax[1].specgram(m + 1e-9, NFFT=2048, Fs=SR, noverlap=1536, cmap="magma", vmin=-120, vmax=-20)
    ax[1].set_yscale("symlog", linthresh=200)
    ax[1].set_ylim(20, 20000)
    fig.tight_layout()
    fig.savefig(str(path), dpi=80)
    plt.close(fig)
