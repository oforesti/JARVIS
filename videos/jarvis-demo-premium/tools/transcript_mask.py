"""Localiza, quadro a quadro, a transcrição ao vivo que o próprio app mostra sob o rótulo "FALANDO".

Na versão premium essa linha duplicava a nossa legenda. Aqui achamos o rótulo ciano (faixa fina de letras
espaçadas logo abaixo das barras da onda), depois o bloco de texto cinza que vem embaixo dele, e gravamos
caixas (em coordenadas do original) + a cor do fundo local, para o palco cobrir com um remendo difuso.

Uso: <venv-audio>/bin/python tools/transcript_mask.py [--at 30,200,...]   → data/tmask.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/source/original.mp4"
W, H = 1920, 1080
FPS = 10
X0, Y0 = 150, 250                     # só a coluna central e a parte de baixo interessam


def bands(mask_rows: np.ndarray, gap: int = 1) -> list[tuple[int, int]]:
    out, i, n = [], 0, len(mask_rows)
    while i < n:
        if mask_rows[i]:
            j = i
            while j < n and (mask_rows[j] or mask_rows[j:j + gap + 1].any()):
                j += 1
            out.append((i, j))
            i = j
        i += 1
    return out


def analyse(fr: np.ndarray):
    f = fr[Y0:, X0:W - X0].astype(np.int16)
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    cyan = (B - R > 45) & (G - R > 40) & (B > 85)     # relativo: vale também nos fades do original
    runs = np.count_nonzero(cyan[:, 1:] & ~cyan[:, :-1], axis=1)
    cand = []
    bl = bands(runs >= 5)
    for k, (a, b) in enumerate(bl):
        h = b - a
        cols = np.flatnonzero(cyan[a:b].any(axis=0))
        if len(cols) == 0:
            continue
        w = cols[-1] - cols[0]
        if not (6 <= h <= 40 and 80 <= w <= 560 and 5 <= w / h <= 22):
            continue
        # a onda fica logo acima e é mais larga que o rótulo
        above = [(a2, b2) for a2, b2 in bl[:k] if b2 >= a - 4 * h and b2 <= a]
        ok = False
        for a2, b2 in above:
            c2 = np.flatnonzero(cyan[a2:b2].any(axis=0))
            if len(c2) and c2[-1] - c2[0] >= 1.3 * w:
                ok = True
        if ok:
            cand.append((a, b, cols[0], cols[-1]))
    if not cand:
        return None
    a, b, c0, c1 = cand[-1]
    s, w, cx = b - a, c1 - c0, (c0 + c1) / 2
    # bloco de texto cinza logo abaixo
    xa, xb = int(max(0, cx - 2.7 * w)), int(min(f.shape[1], cx + 2.7 * w))
    ya, yb = b + 1, int(min(f.shape[0], b + 16 * s))
    reg = f[ya:yb, xa:xb]
    mn, mx = reg.min(axis=2), reg.max(axis=2)
    gray = (mn > max(55, np.median(mn) + 40)) & (mx - mn < 60)
    rows = np.count_nonzero(gray, axis=1) >= max(3, int(0.004 * (xb - xa)))
    lines = bands(rows, gap=max(1, int(0.35 * s)))
    # a transcrição do app é centralizada sob o rótulo; o histórico do chat logo abaixo é alinhado à esquerda
    def centred(la, lb):
        c = np.flatnonzero(gray[la:lb].any(axis=0))
        return len(c) > 0 and abs(xa + (c[0] + c[-1]) / 2 - cx) <= 0.25 * w + 10
    block = []
    for la, lb in lines:
        if not block:
            if la > 4 * s or not centred(la, lb):
                break
            block.append((la, lb))
        elif la - block[-1][1] <= 2.2 * s and centred(la, lb) and len(block) < 4:
            block.append((la, lb))
        else:
            break
    if not block:
        return {"label": [int(cx + X0), int(a + Y0), int(s), int(w)], "box": None}
    ta, tb = block[0][0], block[-1][1]
    cols = np.flatnonzero(gray[ta:tb].any(axis=0))
    if cols[-1] - cols[0] > 5.2 * w:
        return {"label": [int(cx + X0), int(a + Y0), int(s), int(w)], "box": None}
    pad = 0.45 * s
    box = [xa + cols[0] - 1.2 * pad, ya + ta - pad, xa + cols[-1] + 1.2 * pad, ya + tb + pad]
    bg = reg[ta:tb][~gray[ta:tb]]
    col = np.median(bg, axis=0) if len(bg) else np.array([6, 16, 22])
    return {"label": [int(cx + X0), int(a + Y0), int(s), int(w)],
            "box": [int(box[0] + X0), int(box[1] + Y0), int(box[2] + X0), int(box[3] + Y0)],
            "lines": len(block), "bg": "#%02x%02x%02x" % tuple(int(v) for v in col)}


def frames(t0: float, t1: float):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", str(SRC), "-vf", f"fps={FPS}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n, size = 0, W * H * 3
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        try:
            yield t0 + n / FPS, np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        except GeneratorExit:
            p.kill()
            raise
        n += 1
    p.wait()


def main(argv: list[str]) -> None:
    if "--at" in argv:
        for t in [float(x) for x in argv[argv.index("--at") + 1].split(",")]:
            _, fr = next(frames(t, t + 0.3))
            print(t, analyse(fr))
        return
    D = json.loads((ROOT / "data/cues.json").read_text())
    out = []
    for t, fr in frames(D["src_in"], D["src_out"]):
        r = analyse(fr)
        out.append([round(t, 2), r["box"], r["bg"], r["label"][2], r["label"][0], r["label"][1] + r["label"][2] // 2]
                   if r and r["box"] else [round(t, 2), None, None, None, None, None])
    (ROOT / "data/tmask.json").write_text(json.dumps({"fps": FPS, "samples": out}))
    print(f"data/tmask.json: {len(out)} amostras · {sum(1 for x in out if x[1])} com transcrição")


if __name__ == "__main__":
    main(sys.argv)
