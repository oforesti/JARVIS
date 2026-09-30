"""Trailer (~115 s) derivado da versão completa.

Abertura curta própria (compositions/open.html com tempos de trailer) e trechos, em ordem, da versão
completa já renderizada (legendas e grafismos queimados). A voz vem do áudio original no mesmo trecho;
a trilha é própria e os SFX dos grafismos são remapeados da versão completa.

Uso: python3 tools/trailer.py [--no-carve]   →  trailer/index.html + tools/trailer-music-cue.json
Depois: music_long.py tools/trailer-music-cue.json assets/audio/music-trailer.flac e rodar de novo.
"""
from __future__ import annotations

import html as _html
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import OFF, TOTAL as FULL_TOTAL, SIGN_AT, flac_duration  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TR = ROOT / "trailer"
OPEN = {"hook": 0.3, "hookOut": 2.9, "frag": 3.1, "fragK": 0.62, "ignite": 5.2, "note": None,
        "chapter": "TRECHOS DA AUTODEMONSTRAÇÃO", "wmOut": 8.5, "match": 10.0, "appX": 930, "appY": 330, "appR": 140}

# (primeiras palavras, últimas palavras, procurar depois de (s), ato)
EXC = [
    ("Meu nome é Jarvis", "chaves dele", 0, 1),
    ("Todo assistente que você", "Eu guardo", 90, 2),
    ("A outra transforma", "de significado", 140, 2),
    ("Exige que eu fale", "me chamar", 160, 2),
    ("O sistema da sua empresa", "botão eu clico", 260, 3),
    ("Eu vou descrever uma imagem", "alguns segundos", 310, 4),
    ("Essa imagem não estava", "lugar nenhum", 330, 4),
    ("Lembrete, é agora", "que faria", 350, 4),
    ("Eu concordo demais", "concordo demais", 450, 5),
    ("Ele se chama Ultron", "achar o furo", 460, 5),
    ("A trava aqui", "é código", 675, 6),
    ("Ela recusa antes", "de obedecer", 700, 6),
    ("No fim das contas", "245 ferramentas", 712, 7),
    ("Tudo isso roda", "desta casa", 736, 7),
    ("Eu não fui feito", "em casa", 745, 8),
    ("Meu nome é Jarvis", "o que eu faço", 760, 9),
]
BREATH = {5: 0.35, 7: 0.35, 8: 0.5}   # pausa em preto antes do ato (s)
IMPLODE_IN = 737.3                     # o trecho das 245 ferramentas entra na implosão, antes da frase
FLASH = 738.62                         # pico do clarão no núcleo (tempo do original)

W = json.loads((ROOT / "data/transcript.json").read_text())


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(ch for ch in s if not unicodedata.combining(ch)))


NW = [norm(w["text"]) for w in W]


def find(phrase: str, after: float) -> int:
    p = norm(phrase).split()
    for i in range(len(W) - len(p) + 1):
        if W[i]["start"] >= after and NW[i:i + len(p)] == p:
            return i
    raise SystemExit(f"frase não encontrada: {phrase!r} depois de {after}")


def layout() -> tuple[list[dict], float]:
    clips, t = [], OPEN["match"]
    prev_act = None
    for n, (a, b, after, act) in enumerate(EXC):
        i = find(a, after)
        j = find(b, W[i]["start"]) + len(norm(b).split()) - 1
        w0, w1 = W[i]["start"], W[j]["end"]
        pre_lim = W[i - 1]["end"] + 0.05 if i else 0.0
        post_lim = W[j + 1]["start"] - 0.06 if j + 1 < len(W) else w1 + 1
        a_in = max(w0 - 0.28, pre_lim)
        a_out = min(w1 + 0.45, max(post_lim, w1 + 0.08))
        v_in, v_out = a_in, a_out
        if n == 0:                       # a abertura casa no orb: vídeo a partir do início do palco
            v_in, a_in = 9.95, 9.45
        if a.startswith("Tudo isso"):
            v_in = IMPLODE_IN
        if n == len(EXC) - 1:            # até o fim da versão completa (assinatura)
            v_out = FULL_TOTAL - OFF
        if prev_act is not None and act != prev_act:
            t += BREATH.get(act, 0.0)
        c = {"n": n + 1, "act": act, "v_in": round(v_in, 3), "v_out": round(v_out, 3), "a_in": round(a_in, 3), "a_out": round(a_out, 3),
             "t": round(t, 3), "cut": prev_act is not None and act != prev_act, "text": f"{a} … {b}"}
        c["a_t"] = round(t + (a_in - v_in), 3)
        clips.append(c)
        t += v_out - v_in
        prev_act = act
    return clips, round(t, 3)


def full_sfx() -> list[tuple[str, float, float, float]]:
    doc = (ROOT / "index.html").read_text()
    out = []
    for m in re.finditer(r'<audio id="sfx-[^"]*" src="assets/sfx/([^"]+)\.flac" data-start="([\d.]+)" data-duration="([\d.]+)"[^>]*data-volume="([\d.]+)"', doc):
        out.append((m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))))
    return out


def sfx_plan(clips: list[dict], total: float) -> list[tuple[str, float, float]]:
    S: list[tuple[str, float, float]] = []
    add = lambda f, t, v: S.append((f, round(t, 3), v))
    O, K, F0 = OPEN, OPEN["fragK"], OPEN["frag"]
    # abertura (mesma paleta da versão completa, no ritmo do trailer)
    add("electric", 0.1, 0.24); add("pulse-a", O["hook"] + 0.1, 0.16); add("boot", F0 - 0.2, 0.2)
    for t, f, v in [(3.40, "ui-click-1", .36), (4.00, "pulse-c", .22), (4.50, "ui-click-2", .32), (4.94, "ui-click-3", .32), (5.32, "tick", .4),
                    (5.66, "ui-click-1", .3), (5.96, "tick", .36), (6.20, "pulse-b", .2), (6.40, "tick", .32), (6.56, "ui-click-2", .26)]:
        add(f, F0 + (t - 3.4) * K, v)
    add("riser-long", O["ignite"] - 3.22, 0.34); add("glitch-1", O["ignite"] - 0.12, 0.16)
    add("hit-sub-2", O["ignite"], 0.5); add("sub-drop", O["ignite"], 0.28); add("whoosh-soft-3", O["ignite"] + 0.95, 0.3)
    add("ui-click-soft", O["ignite"] + 1.4, 0.14); add("sweep-up", O["match"] - 2.65, 0.16); add("whoosh-deep", O["match"] - 1.3, 0.14)
    # grafismos queimados de cada trecho: os mesmos sons da versão completa, no novo tempo
    for c in clips:
        f_in, f_out = c["v_in"] + OFF, c["v_out"] + OFF
        for f, s, d, v in full_sfx():
            if s >= 13.0 and f_in - 0.05 <= s < f_out - 0.1:
                add(f, c["t"] + (s - f_in), v)
    # trocas de ato: sopro curto; nas pausas, um grave macio
    wh = ["whoosh-soft-1", "whoosh-soft-2", "whoosh-soft-3"]
    for k, c in enumerate(x for x in clips if x["cut"]):
        gap = BREATH.get(c["act"], 0.0)
        add(wh[k % 3], c["t"] - gap - 0.3, 0.12)
        if gap:
            add("hit-soft", c["t"] - gap, 0.22)
    return [(f, t, v) for f, t, v in S if t < total - 0.05]


def music_cue(clips: list[dict], total: float) -> dict:
    act = {}
    for c in clips:
        act.setdefault(c["act"], c["t"])
    I, M = OPEN["ignite"], OPEN["match"]
    last = clips[-1]
    sign = last["t"] + (SIGN_AT - (last["v_in"] + OFF))
    imp = next(c for c in clips if c["text"].startswith("Tudo isso"))
    flash = imp["t"] + (FLASH - imp["v_in"])
    S = lambda name, a, b, **k: {"name": name, "start": round(a, 3), "end": round(b, 3), **k}
    return {"length": round(total + 0.35, 3), "bpm": 100.0, "grid_anchor": I, "target_lufs": -18, "sections": [
        S("intro", 0, I, energy=0.12, layers=["drone", "air"], level_db=-15, ramp=2.5, chord="Dm9"),
        S("reveal", I, M - 1.1, energy=0.35, layers=["pad", "drone"], level_db=-7, ramp=0.05, chord="Dm9", breath_before=0.38),
        S("a1", M - 1.1, act[2], energy=0.3, layers=["pad", "ticks"], level_db=-13, ramp=0.6),
        S("a2", act[2], act[3], energy=0.4, layers=["pad", "arp"], level_db=-13, ramp=0.6),
        S("a3", act[3], act[5], energy=0.5, layers=["pad", "arp", "bass"], level_db=-12, ramp=0.6),
        S("a4", act[5], act[6], energy=0.35, layers=["pad", "drone"], level_db=-13, ramp=0.6, chord="Bbmaj9", breath_before=BREATH[5]),
        S("a5", act[6], act[7], energy=0.4, layers=["pad", "arp"], level_db=-13, ramp=0.6),
        S("climax", act[7], act[8], energy=0.7, layers=["pad", "arp", "bass", "drums"], level_db=-12, ramp=1.0, kit="pulse", breath_before=BREATH[7]),
        S("origin", act[8], act[9], energy=0.25, layers=["pad", "drone"], level_db=-15, ramp=1.0, breath_before=BREATH[8]),
        S("fecho", act[9], sign, energy=0.4, layers=["pad", "arp"], level_db=-13, ramp=1.0),
        S("final", sign, total + 0.35, energy=0.3, layers=["drone", "air", "pad"], level_db=-8, ramp=0.05, chord="Dmaj9", breath_before=0.5),
    ], "motifs": [{"t": round(I + 0.95, 3), "gain": 0.26}, {"t": round(sign + 0.9 + 1.2, 3), "gain": 0.42}],
        "toms": [I, round(flash, 3)]}


def automation(points: list[tuple[float, float]]) -> str:
    lane = {"version": 1, "lanes": [{"target": "volume", "points": [{"t": round(a, 3), "v": b} for a, b in points]}]}
    return _html.escape(json.dumps(lane))


def ensure_project() -> None:
    TR.mkdir(exist_ok=True)
    (TR / "media").mkdir(exist_ok=True)
    for name, target in [("assets", "../assets"), ("compositions", "../compositions"), ("node_modules", "../node_modules"),
                         ("media/completo.mp4", "../../renders/jarvis-demo-completo.mp4")]:
        p = TR / name
        if not p.is_symlink():
            os.symlink(target, p)
    (TR / "hyperframes.json").write_text((ROOT / "hyperframes.json").read_text())
    (TR / "meta.json").write_text(json.dumps({"id": "jarvis-demo-trailer", "name": "jarvis-demo-trailer", "createdAt": "2026-09-30T17:00:00.000Z"}, indent=2) + "\n")
    pk = json.loads((ROOT / "package.json").read_text())
    pk["name"] = "jarvis-demo-trailer"
    (TR / "package.json").write_text(json.dumps(pk, indent=2) + "\n")


def main(argv: list[str]) -> None:
    ensure_project()
    clips, total = layout()
    (ROOT / "tools/trailer-music-cue.json").write_text(json.dumps(music_cue(clips, total), indent=1))
    for c in clips:
        print(f"{c['n']:2d} ato {c['act']} {c['t']:6.2f}–{c['t'] + c['v_out'] - c['v_in']:6.2f}  orig {c['v_in']:.2f}–{c['v_out']:.2f}  {c['text']}")
    vids, auds, dips = [], [], []
    for c in clips:
        d = round(c["v_out"] - c["v_in"], 3)
        vids.append(f'      <video id="v-{c["n"]:02d}" class="clip" src="media/completo.mp4" muted playsinline data-start="{c["t"]}" '
                    f'data-duration="{d}" data-media-start="{round(c["v_in"] + OFF, 3)}" data-track-index="1"></video>')
        ad = round(c["a_out"] - c["a_in"], 3)
        env = automation([(0, 0), (0.04, 1), (ad - 0.07, 1), (ad, 0)])
        auds.append(f'      <audio id="vo-{c["n"]:02d}" src="assets/source/original-audio.flac" data-start="{c["a_t"]}" data-duration="{ad}" '
                    f'data-media-start="{c["a_in"]}" data-track-index="{10 + c["n"] % 2}" data-audio-group="voiceover" data-volume="1" data-automation="{env}"></audio>')
        if c["cut"]:
            dips.append([round(c["t"] - BREATH.get(c["act"], 0.0), 3), round(c["t"], 3)])
    lanes: list[float] = []
    for f, t, v in sorted(sfx_plan(clips, total), key=lambda x: x[1]):
        dur = round(min(flac_duration(ROOT / f"assets/sfx/{f}.flac") + 0.0005, total - t), 3)
        lane = next((i for i, e in enumerate(lanes) if e <= t - 0.01), None)
        if lane is None:
            lanes.append(0.0); lane = len(lanes) - 1
        lanes[lane] = t + dur
        auds.append(f'      <audio id="sfx-{len(auds):03d}-{f}" src="assets/sfx/{f}.flac" data-start="{t}" data-duration="{dur}" '
                    f'data-track-index="{30 + lane}" data-audio-group="sfx" data-volume="{v}"></audio>')
    music = ROOT / "assets/audio/music-trailer.flac"
    mtag = (f'      <audio id="music-bed" src="assets/audio/music-trailer.flac" data-start="0" data-duration="{total}" '
            f'data-track-index="20" data-audio-group="music" data-volume="0.9"></audio>') if music.exists() else ""
    doc = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>J.A.R.V.I.S. — trailer</title>
    <script src="assets/vendor/gsap/gsap.min.js"></script>
    <script src="assets/vendor/gsap/CustomEase.min.js"></script>
    <script src="assets/vendor/gsap/DrawSVGPlugin.min.js"></script>
    <script src="assets/js/jarvis-motion.js"></script>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.OPEN = {json.dumps(OPEN, ensure_ascii=False)};
    </script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #04080c; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #04080c; }}
      #root > div[data-composition-src] {{ position: absolute; inset: 0; }}
      video.clip {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }}
      #dip {{ position: absolute; inset: 0; background: #04080c; opacity: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">
{chr(10).join(vids)}
      <div id="el-open" data-composition-id="open" data-composition-src="compositions/open.html"
        data-start="0" data-duration="{OPEN['match']}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
      <div id="dip" data-layout-ignore></div>
{mtag}
{chr(10).join(auds)}
    </div>
    <script>
      (function () {{
        const tl = gsap.timeline({{ paused: true }});
        // trocas de ato: mergulho curto no preto (com pausa quando o ato pede respiro)
        {json.dumps(dips)}.forEach(([a, b]) => {{
          tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.18, ease: "power2.in", immediateRender: false }}, a - 0.18);
          tl.fromTo("#dip", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.3, ease: "power2.out", immediateRender: false }}, b + 0.02);
        }});
        window.__timelines["main"] = tl;
      }})();
    </script>
  </body>
</html>
"""
    (TR / "index.html").write_text(doc)
    carve = Path.home() / ".claude/skills/hyperframes-audio/scripts/carve.mjs"
    if mtag and carve.exists() and "--no-carve" not in argv:
        r = subprocess.run(["node", str(carve), "--comp", "index.html", "--bed", "music-bed"], cwd=TR, capture_output=True, text=True)
        print("carve:", (r.stdout.strip().splitlines() or ["?"])[-1] if r.returncode == 0 else "FALHOU\n" + r.stderr[-600:])
    print(f"trailer/index.html: {total:.1f}s · {len(clips)} trechos · {len(auds) - len(clips)} SFX · música {'ok' if mtag else 'ausente'}")


if __name__ == "__main__":
    main(sys.argv)
