"""Monta a versão completa premium: index.html, legendas, plano de SFX, roteiro da trilha e carve.

Uso: python tools/build.py [--music-cue-only] [--no-carve]
Antes: python tools/transcript_fix.py && python tools/cues.py
Trilha: python tools/audio/music.py tools/music-cue.json <dir> → assets/audio/music.flac
"""
from __future__ import annotations

import html as _html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_IN, SRC_OUT = 9.95, 773.8     # 9.95: fim da cartela "Capítulo 1" do original, o app surge em seguida
AUDIO_IN = 9.45                    # a voz começa ("Meu nome é Jarvis", 9.52) enquanto o núcleo encaixa
STAGE_AT = 13.0                    # a gravação entra por baixo do fim da abertura
OFF = STAGE_AT - SRC_IN            # tempo do filme = tempo do original + OFF
SIGN_AT = 771.0 + OFF              # a assinatura começa logo depois de "…o que eu faço."
TOTAL = round(SIGN_AT + 8.4, 3)
OPEN = {"hook": 0.45, "hookOut": 3.0, "ignite": 6.8, "note": 9.5, "wmOut": 10.9, "match": 13.0, "appX": 930, "appY": 330, "appR": 140}
SIGN = {"ign": 0.9, "end": round(TOTAL - SIGN_AT, 3)}
KEYWORDS = ["computador", "245", "vetor", "lembrete", "botão", "visão", "simulo", "Ultron", "sintetizo", "trava", "máquina", "empresa"]
TOP_WINDOWS = [[349.2 + OFF, 363.2 + OFF]]   # pop-up do lembrete embaixo → legenda sobe


def flac_duration(path: Path) -> float:
    b = path.read_bytes()[:42]
    si = b[8:42]
    sr = (si[10] << 12) | (si[11] << 4) | (si[12] >> 4)
    total = ((si[13] & 0x0F) << 32) | (si[14] << 24) | (si[15] << 16) | (si[16] << 8) | si[17]
    return total / sr


def F(src_t: float) -> float:
    return round(src_t + OFF, 3)


def sfx_plan(cues: list[dict]) -> list[tuple[str, str, float, float]]:
    S: list[tuple[str, str, float, float]] = []
    n = [0]

    def add(file, t, vol):
        n[0] += 1
        S.append((f"sfx-{n[0]:03d}-{file}", file, round(t, 3), vol))

    # abertura
    add("electric", 0.1, 0.24); add("pulse-a", OPEN["hook"] + 0.1, 0.16); add("boot", 3.2, 0.22)
    for t, f, v in [(3.40, "ui-click-1", .36), (4.00, "pulse-c", .22), (4.50, "ui-click-2", .32), (4.94, "ui-click-3", .32), (5.32, "tick", .4),
                    (5.66, "ui-click-1", .3), (5.96, "tick", .36), (6.20, "pulse-b", .2), (6.40, "tick", .32), (6.56, "ui-click-2", .26)]:
        add(f, t, v)
    add("riser-long", 3.6, 0.36); add("glitch-1", 6.68, 0.16)
    add("hit-sub-2", OPEN["ignite"], 0.5); add("sub-drop", OPEN["ignite"], 0.28); add("whoosh-soft-3", OPEN["ignite"] + 0.95, 0.3)
    add("ui-click-soft", OPEN["note"], 0.14); add("sweep-up", OPEN["match"] - 2.65, 0.16); add("whoosh-deep", OPEN["match"] - 1.3, 0.14)   # a subida termina no corte; "Meu nome é Jarvis" limpo
    # por cima da demo (discreto: a gravação já tem os sons do próprio app)
    wh = ["whoosh-soft-1", "whoosh-soft-2", "whoosh-soft-3"]
    k = 0
    for c in cues:
        kd = c["k"]
        if kd == "chapter":
            add("whoosh-deep", F(c["t0"]) - 0.3, 0.22); add("hit-soft", F(c["t0"]) + 0.08, 0.22); add("sweep-up", F(c["t0"]) + 0.85, 0.14)
        elif kd == "kin":
            add(wh[k % 3], F(c["t"]) - 0.08, 0.16); k += 1
        elif kd in ("res", "hud"):
            add("ui-click-soft", F(c["t"]), 0.24)
            if kd == "hud":
                for it in c["items"]:
                    add("tick", F(it[2]), 0.16)
        elif kd == "call":
            add("ui-click-1", F(c["t"]), 0.2)
        elif kd == "boxes":
            add("scan", F(c["t"]), 0.18)
            for r in c.get("regions", []):
                add("lock-in", F(r[1]), 0.16)
        elif kd == "chip":
            add("pulse-a", F(c["t0"]), 0.18); add("confirm", F(c["t1"]), 0.3)
        elif kd == "dia":
            add("pulse-b", F(c["t"]), 0.2)
            if c["kind"] == "converge":
                for lab, t in c["chips"]:
                    add("tick", F(t), 0.16)
                add("data-stream-1", F(c["t_count"]), 0.16)
                add("whoosh-soft-2", F(c["t"] + c["d"]) - 1.0, 0.14)   # as ferramentas voltam ao núcleo
                add("hit-sub-1", F(c["t"] + c["d"]) - 0.12, 0.5)
            if c["kind"] == "beats4":
                for s in c["steps"]:
                    add("lock-in", F(s[2]), 0.16)
            if c["kind"] == "lock":
                add("lock-in", F(c["t_code"]), 0.22); add("ui-click-2", F(c["t_refuse"]), 0.2)
    # assinatura
    add("reverse-impact", SIGN_AT + SIGN["ign"] - 0.9, 0.24)
    add("signature", SIGN_AT + SIGN["ign"], 0.6)
    add("whoosh-soft-3", SIGN_AT + SIGN["ign"] + 0.95, 0.22)
    return S


def tmask_events() -> list:
    """Remendo sobre a transcrição ao vivo do app (data/tmask.json, tools/transcript_mask.py).

    Eventos em tempo do original: [t, vaga, x0, y0, x1, y1, cor, spread, blur, instantâneo] mostra/move;
    [t, vaga, None, instantâneo] some. Entre amostras a caixa é a união das vizinhas (o texto não escapa),
    exceto nos cortes do próprio original (o rótulo salta): aí a outra vaga assume, com um intervalo de
    sobreposição, sem cobrir o espaço entre os dois enquadramentos.
    """
    p = ROOT / "data/tmask.json"
    if not p.exists():
        return []
    D = json.loads(p.read_text())
    S, dt = D["samples"], 1.0 / D["fps"]
    n = len(S)
    for i in range(1, n):                     # buracos de até 2 amostras: segue a caixa anterior
        if S[i][1] is None and S[i - 1][1] is not None and any(S[k][1] is not None for k in range(i + 1, min(n, i + 3))):
            S[i] = [S[i][0], *S[i - 1][1:]]
    rgb = lambda h: [int(h[k:k + 2], 16) for k in (1, 3, 5)]
    disp = lambda a, b: abs(a[4] - b[4]) + abs(a[5] - b[5])
    big = lambda a, b: disp(a, b) > 2.5 * max(a[3], b[3]) or abs(a[3] - b[3]) > 0.35 * max(a[3], b[3])
    still = lambda a, b: disp(a, b) <= 0.4 * max(a[3], b[3]) and abs(a[3] - b[3]) <= 0.1 * max(a[3], b[3])
    union = lambda p, q: [min(p[0], q[0]), min(p[1], q[1]), max(p[2], q[2]), max(p[3], q[3])]
    ev, slot, i = [], 0, 0
    while i < n:
        if S[i][1] is None:
            i += 1
            continue
        j = i
        while j + 1 < n and S[j + 1][1] is not None:
            j += 1
        if S[j][0] - S[i][0] >= 0.35:         # corridas curtíssimas são ruído
            # corte = salto isolado do rótulo; movimento = passos seguidos (zoom do original); parado = união
            kind = {}
            for k in range(i, j):
                A, B = S[k], S[k + 1]
                if big(A, B) and (k == i or still(S[k - 1], A)) and (k + 1 == j or still(B, S[k + 2])):
                    kind[k] = "cut"
                else:
                    kind[k] = "still" if still(A, B) else "move"
            segs, a = [], i
            for k in range(i, j):
                if kind[k] == "cut":
                    segs.append((a, k))
                    a = k + 1
            segs.append((a, j))
            for m, (a, b) in enumerate(segs):
                first, last = m == 0, m == len(segs) - 1
                sz = lambda k: max(S[k][3], S[min(k + 1, b)][3])
                box0 = union(S[a][1], S[a + 1][1]) if a < b and kind[a] == "still" else S[a][1]
                ev.append([round(S[a][0] - (0.15 if first else dt), 2), slot, *box0, S[a][2], round(0.3 * sz(a)), round(0.7 * sz(a)), 1 if not first else 0])
                cur = box0
                for k in range(a, b):
                    A, B = S[k], S[k + 1]
                    if kind[k] == "move":        # acompanha o zoom do original, sem união
                        ev.append([round(A[0], 2), slot, *B[1], B[2], round(0.3 * sz(k)), round(0.7 * sz(k)), 2])
                        cur = B[1]
                    else:
                        box = union(A[1], B[1]) if k + 1 <= b else A[1]
                        if any(abs(u - v) > 3 for u, v in zip(box, cur)):
                            ev.append([round(A[0], 2), slot, *box, A[2], round(0.3 * sz(k)), round(0.7 * sz(k)), 0])
                            cur = box
                ev.append([round(S[b][0] + (0.2 if last else dt), 2), slot, None, 0 if last else 1])
                slot ^= 1
        i = j + 1
    ev.sort(key=lambda e: e[0])
    return ev


def music_cue() -> dict:
    f = F
    sec = [
        ("intro", 0, OPEN["ignite"], 0.12, ["drone", "air"], "Dm9", -15, 2.5, None),
        ("reveal", OPEN["ignite"], F(AUDIO_IN) - 0.6, 0.35, ["pad", "drone"], "Dm9", -7, 0.05, 0.38),   # sai antes da primeira fala
        ("c1", F(AUDIO_IN) - 0.6, f(94.8), 0.3, ["pad", "ticks"], None, -13, 0.6, None),
        ("c2", f(94.8), f(192.8), 0.4, ["pad", "arp"], None, -13, 0.6, None),
        ("c3", f(192.8), f(306.4), 0.45, ["pad", "arp", "bass"], None, -12, 0.6, None),
        ("c4", f(306.4), f(380.0), 0.4, ["pad", "arp"], "Bbmaj9", -13, 0.6, None),
        ("c5", f(380.0), f(448.4), 0.5, ["pad", "arp", "bass"], None, -12, 0.6, None),
        ("c6", f(448.4), f(532.0), 0.35, ["pad", "drone"], "Bbmaj9", -13, 0.6, None),
        ("c7a", f(532.0), f(541.8), 0.3, ["pad"], None, -14, 0.6, None),
        ("jazz", f(541.8), f(558.5), 0.1, ["air"], None, -60, 0.8, None),        # a rádio do app toca
        ("c7b", f(558.5), f(589.5), 0.3, ["pad", "ticks"], None, -14, 1.2, None),
        ("sons", f(589.5), f(630.5), 0.1, ["air"], None, -60, 0.8, None),        # os sons sintetizados do app
        ("c8", f(630.5), f(713.3), 0.4, ["pad", "arp"], None, -13, 1.2, None),
        ("fim", f(713.3), f(738.5), 0.7, ["pad", "arp", "bass", "drums"], None, -12, 1.5, None),
        ("climax", f(738.5), f(749.0), 0.6, ["pad", "arp", "bass"], None, -11, 0.8, None),
        ("origem", f(749.0), f(762.9), 0.25, ["pad", "drone"], None, -15, 1.2, None),     # "escrito por uma pessoa, em casa": só o chão
        ("fecho", f(762.9), f(771.0), 0.4, ["pad", "arp"], None, -13, 1.0, None),
        ("final", SIGN_AT, TOTAL + 0.4, 0.3, ["drone", "air", "pad"], "Dmaj9", -8, 0.05, 0.5),
    ]
    out = []
    for name, a, b, en, layers, chord, lv, ramp, br in sec:
        s = {"name": name, "start": round(a, 3), "end": round(b, 3), "energy": en, "layers": layers, "level_db": lv, "ramp": ramp}
        if chord:
            s["chord"] = chord
        if br:
            s["breath_before"] = br
        if "drums" in layers:
            s["kit"] = "pulse"
        out.append(s)
    return {"length": round(TOTAL + 0.4, 3), "bpm": 100.0, "grid_anchor": OPEN["ignite"], "target_lufs": -18, "sections": out,
            "motifs": [{"t": OPEN["ignite"] + 0.95, "gain": 0.26}, {"t": round(SIGN_AT + SIGN["ign"] + 1.2, 3), "gain": 0.42}],
            "toms": [OPEN["ignite"]]}


def main(argv: list[str]) -> None:
    D = json.loads((ROOT / "data/cues.json").read_text())
    (ROOT / "tools/music-cue.json").write_text(json.dumps(music_cue(), indent=1))
    if "--music-cue-only" in argv:
        return
    # legendas (tempo do filme)
    W = json.loads((ROOT / "data/transcript.json").read_text())
    words = [{"text": w["text"], "start": F(w["start"]), "end": F(w["end"])} for w in W if w["caption"]]
    cap = (ROOT / "compositions/captions.html").read_text()
    cap = re.sub(r"var TRANSCRIPT = \[.*?\];", lambda m: "var TRANSCRIPT = " + json.dumps(words, ensure_ascii=False) + ";", cap, flags=re.S)
    cap = re.sub(r"var KEYWORDS = \[.*?\];", lambda m: "var KEYWORDS = " + json.dumps(KEYWORDS, ensure_ascii=False) + ";", cap, flags=re.S)
    cap = re.sub(r"var TOP_WINDOWS = \[.*?\];", lambda m: "var TOP_WINDOWS = " + json.dumps(TOP_WINDOWS) + ";", cap, flags=re.S)
    (ROOT / "compositions/captions.html").write_text(cap)

    audio = [f'      <audio id="vo-original" src="assets/source/original-audio.flac" data-start="{F(AUDIO_IN)}" data-media-start="{AUDIO_IN}" '
             f'data-duration="{round(SRC_OUT - AUDIO_IN, 3)}" data-track-index="10" data-audio-group="voiceover" data-volume="1"></audio>']
    lanes: list[float] = []
    for name, file, t, vol in sorted(sfx_plan(D["cues"]), key=lambda x: x[2]):
        dur = round(min(flac_duration(ROOT / f"assets/sfx/{file}.flac") + 0.0005, TOTAL - t), 3)
        lane = next((i for i, e in enumerate(lanes) if e <= t - 0.01), None)
        if lane is None:
            lanes.append(0.0); lane = len(lanes) - 1
        lanes[lane] = t + dur
        audio.append(f'      <audio id="{name}" src="assets/sfx/{file}.flac" data-start="{t}" data-duration="{dur}" '
                     f'data-track-index="{30 + lane}" data-audio-group="sfx" data-volume="{vol}"></audio>')
    music = ROOT / "assets/audio/music.flac"
    mtag = (f'      <audio id="music-bed" src="assets/audio/music.flac" data-start="0" data-duration="{TOTAL}" '
            f'data-track-index="20" data-audio-group="music" data-volume="0.9"></audio>') if music.exists() else ""
    js = json.dumps(D, ensure_ascii=False)
    doc = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>J.A.R.V.I.S. — autodemonstração (versão premium)</title>
    <script src="assets/vendor/gsap/gsap.min.js"></script>
    <script src="assets/vendor/gsap/CustomEase.min.js"></script>
    <script src="assets/vendor/gsap/DrawSVGPlugin.min.js"></script>
    <script src="assets/js/jarvis-motion.js"></script>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.CUES = {js};
      window.OPEN = {json.dumps(OPEN)};
      window.SIGN = {json.dumps(SIGN)};
      window.TMASK = {{"dt": 0.1, "ev": {json.dumps(tmask_events())}}};
    </script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #04080c; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #04080c; }}
      #root > div[data-composition-src] {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="el-stage" data-composition-id="stage" data-composition-src="compositions/stage.html"
        data-start="{STAGE_AT}" data-duration="{round(SRC_OUT - SRC_IN, 3)}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
      <div id="el-open" data-composition-id="open" data-composition-src="compositions/open.html"
        data-start="0" data-duration="{OPEN['match'] + 0.8}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
      <div id="el-captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
        data-start="0" data-duration="{TOTAL}" data-track-index="5" data-track-kind="captions" data-width="1920" data-height="1080"></div>
      <div id="el-sign" data-composition-id="sign" data-composition-src="compositions/sign.html"
        data-start="{round(SIGN_AT, 3)}" data-duration="{SIGN['end']}" data-track-index="3" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
{mtag}
{chr(10).join(audio)}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(doc)
    carve = Path.home() / ".claude/skills/hyperframes-audio/scripts/carve.mjs"
    if mtag and carve.exists() and "--no-carve" not in argv:
        r = subprocess.run(["node", str(carve), "--comp", "index.html", "--bed", "music-bed"], cwd=ROOT, capture_output=True, text=True)
        print("carve:", (r.stdout.strip().splitlines() or ["?"])[-1] if r.returncode == 0 else "FALHOU\n" + r.stderr[-600:])
    print(f"index.html: {TOTAL:.1f}s · {len(D['cues'])} deixas · {len(audio) - 1} SFX · música {'ok' if mtag else 'ausente'}")


if __name__ == "__main__":
    main(sys.argv)
