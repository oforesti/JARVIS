"""Monta o index.html a partir de timeline.json — cenas, voz, legendas, trilha e SFX.

Uso: python tools/assemble.py [--music-cue-only] [--no-carve] [--sem-narracao]

- Escreve `index.html` (raiz fina: hosts das cenas, trilha de legendas, áudio).
- Injeta `window.JT` (linha do tempo) no <head> para as cenas sincronizarem com a fala.
- Reescreve `var TRANSCRIPT` e `var KEYWORDS` em compositions/captions.html.
- Escreve `tools/music-cue.json` para `tools/audio/music.py`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def flac_duration(path: Path) -> float:
    """Duração lida do bloco STREAMINFO do FLAC (sem dependências)."""
    b = path.read_bytes()[:42]
    assert b[:4] == b"fLaC", path
    si = b[8:42]
    sr = (si[10] << 12) | (si[11] << 4) | (si[12] >> 4)
    total = ((si[13] & 0x0F) << 32) | (si[14] << 24) | (si[15] << 16) | (si[16] << 8) | si[17]
    return total / sr

# palavra de destaque (ciano) por fala legendada — no máximo uma por frase
KEYWORDS = ["falar", "voz", "funções", "Elo", "memória", "ferramenta", "aprova"]

# SFX: (id, arquivo, tempo absoluto ou (marca|frame, deslocamento), volume)
def sfx_plan(tl: dict) -> list[tuple[str, str, float, float]]:
    fr = {f["id"][:3]: f for f in tl["frames"]}
    m = tl["marks"]
    vo = {v["id"]: v for v in tl["vo"]}
    S = []

    def add(name, file, t, vol):
        S.append((name, file, round(t, 3), vol))

    # F01 — abertura
    add("sfx-electric", "electric", 0.15, 0.2)
    add("sfx-scan-open", "scan", 0.30, 0.13)
    add("sfx-boot", "boot", 1.10, 0.22)
    for k, (t, f, v) in enumerate([(1.20, "ui-click-1", .36), (1.85, "pulse-c", .2), (2.40, "ui-click-2", .34),
                                   (2.90, "ui-click-3", .45), (3.30, "tick", .55), (3.66, "ui-click-1", .4),
                                   (3.98, "tick", .5), (4.24, "pulse-b", .26), (4.44, "tick", .45)]):
        add(f"sfx-frag-{k}", f, t, v)
    add("sfx-flash-name", "glitch-1", 4.58, 0.22)
    add("sfx-ready", "confirm-low", 4.62, 0.26)
    add("sfx-riser", "riser-long", 2.0, 0.38)
    add("sfx-ignite", "hit-sub-2", m["reveal"], 0.85)
    add("sfx-ignite-sub", "sub-drop", m["reveal"], 0.42)
    add("sfx-wordmark", "whoosh-soft-3", m["reveal"] + 0.95, 0.32)
    add("sfx-dive", "sweep-up", fr["f01"]["end"] - 1.15, 0.42)
    add("sfx-dive-whoosh", "whoosh-deep", fr["f01"]["end"] - 0.55, 0.46)
    # F02
    f = fr["f02"]["start"]
    add("sfx-land", "hit-soft", f + 0.02, 0.4)
    add("sfx-phone-lock", "lock-in", f + 1.75, 0.34)
    add("sfx-kicker", "pulse-a", f + 3.55, 0.24)
    add("sfx-spot", "scan", f + 4.3, 0.2)
    add("sfx-callout", "ui-click-soft", f + 5.9, 0.45)
    # F03 — um som por verbo, na entrada da voz
    f = fr["f03"]["start"]
    add("sfx-cut-black", "sub-drop", f, 0.12)
    verb_sfx = ["ui-click-1", "tick", "whoosh-soft-1", "hit-soft", "confirm", "pulse-b", "scan"]
    verb_vol = [0.5, 0.55, 0.24, 0.18, 0.18, 0.22, 0.18]
    for k, (v, s, vol) in enumerate(zip(m["verbs"], verb_sfx, verb_vol)):
        add(f"sfx-verb-{k}", s, v["at"] - 0.02, vol)
    add("sfx-type-a", "tick", m["verbs"][1]["at"] + 0.18, 0.4)
    add("sfx-type-b", "tick", m["verbs"][1]["at"] + 0.34, 0.35)
    add("sfx-push-04", "whoosh-soft-2", fr["f04"]["start"] - 0.45, 0.34)
    # F04
    add("sfx-count", "data-stream-2", m["count_start"] - 0.05, 0.22)
    add("sfx-areas", "data-stream-1", m["areas_at"] - 0.05, 0.2)
    add("sfx-risk", "ui-click-2", m["risk_at"], 0.42)
    add("sfx-dive-05", "whoosh-soft-1", fr["f05"]["start"] - 0.5, 0.34)
    # F05
    f = fr["f05"]["start"]
    add("sfx-listen", "pulse-a", f + 2.05, 0.26)
    for k in range(10):
        add(f"sfx-key-{k}", "tick", m["type_start"] + 0.08 + k * 0.22, 0.28 + 0.04 * (k % 3))
    add("sfx-step-1", "lock-in", m["step1_at"], 0.36)
    add("sfx-step-2", "lock-in", m["step2_at"], 0.36)
    add("sfx-done", "confirm", m["step2_at"] + 0.9, 0.28)
    # F06
    f = fr["f06"]["start"]
    add("sfx-wipe-06", "sweep-down", f - 0.35, 0.3)
    add("sfx-elo-link", "whoosh-deep", f + 1.2, 0.36)
    add("sfx-elo-data", "data-stream-2", f + 2.2, 0.2)
    for k, t in enumerate([m["elo_wake"], m["elo_screen"], m["elo_share"], m["elo_share"] + 0.55]):
        add(f"sfx-elo-chip-{k}", "pulse-a" if k % 2 == 0 else "pulse-c", t, 0.28)
    # F07
    f = fr["f07"]["start"]
    add("sfx-code-open", "whoosh-soft-3", f + 0.5, 0.3)
    for k in range(12):
        add(f"sfx-code-key-{k}", "tick", m["code_start"] + 0.55 + k * 0.16, 0.22 + 0.05 * (k % 2))
    add("sfx-review", "scan", m["review_at"] - 0.1, 0.26)
    add("sfx-approve", "ui-click-1", m["approve_at"] - 0.05, 0.6)
    add("sfx-approve-ok", "confirm", m["approve_at"] + 0.1, 0.3)
    add("sfx-card-lock", "lock-in", fr["f07"]["end"] - 0.63, 0.36)
    add("sfx-split", "whoosh-soft-1", fr["f07"]["end"] - 0.42, 0.3)
    # F08
    f = fr["f08"]["start"]
    add("sfx-cards", "whoosh-soft-2", f + 0.45, 0.34)
    add("sfx-memory", "pulse-a", f + 4.3, 0.24)
    add("sfx-ultron", "sweep-down", m["ultron_at"] - 0.1, 0.24)
    add("sfx-glitch-out", "glitch-2", fr["f08"]["end"] - 0.32, 0.26)
    # F09
    f = fr["f09"]["start"]
    add("sfx-final-ignite", "signature", m["final_ignition"], 0.5)
    add("sfx-final-name", "whoosh-soft-3", m["final_ignition"] + 0.95, 0.14)
    add("sfx-cta", "confirm-low", m["cta_at"] + 0.05, 0.2)
    return S


def music_cue(tl: dict) -> dict:
    fr = {f["id"][:3]: f for f in tl["frames"]}
    m = tl["marks"]
    return {
        "length": round(tl["duration"] + 0.4, 3), "bpm": tl["bpm"], "grid_anchor": tl["anchor"], "target_lufs": -18,
        "sections": [
            {"name": "intro", "start": 0, "end": m["reveal"], "energy": 0.12, "layers": ["drone", "air"], "chord": "Dm9", "level_db": -15, "ramp": 2.5},
            {"name": "reveal", "start": m["reveal"], "end": fr["f02"]["start"], "energy": 0.35, "layers": ["pad", "drone"], "chord": "Dm9", "level_db": -7, "ramp": 0.05, "breath_before": 0.38},
            {"name": "discovery", "start": fr["f02"]["start"], "end": fr["f03"]["start"], "energy": 0.45, "layers": ["pad", "arp", "ticks"], "prog_offset": 1, "level_db": -7, "ramp": 0.6},
            {"name": "turn", "start": fr["f03"]["start"], "end": m["verbs"][0]["at"] - 0.3, "energy": 0.3, "layers": ["pad", "ticks"], "chord": "Bbmaj9", "level_db": -9, "ramp": 0.05},
            {"name": "verbs", "start": m["verbs"][0]["at"] - 0.3, "end": fr["f04"]["start"], "energy": 0.68, "layers": ["pad", "arp", "bass", "drums"], "kit": "pulse", "level_db": -6, "ramp": 0.1},
            {"name": "scale", "start": fr["f04"]["start"], "end": fr["f05"]["start"], "energy": 0.78, "layers": ["pad", "arp", "bass", "drums"], "kit": "half", "level_db": -3, "ramp": 0.3},
            {"name": "chain", "start": fr["f05"]["start"], "end": m["breath_elo"][1], "energy": 0.6, "layers": ["pad", "arp", "bass", "drums"], "kit": "pulse", "level_db": -5, "ramp": 0.6},
            {"name": "climax", "start": m["breath_elo"][1], "end": fr["f08"]["start"], "energy": 0.95, "layers": ["pad", "arp", "bass", "drums"], "kit": "half", "level_db": 0, "ramp": 0.05, "breath_before": 0.45},
            {"name": "personas", "start": fr["f08"]["start"], "end": fr["f09"]["start"], "energy": 0.7, "layers": ["pad", "bass", "drums", "arp"], "kit": "pulse", "chord": "Bbmaj9", "level_db": -4, "ramp": 0.4},
            {"name": "breath", "start": fr["f09"]["start"], "end": m["final_ignition"], "energy": 0.18, "layers": ["drone", "air"], "chord": "Bbmaj9", "level_db": -15, "ramp": 0.3},
            {"name": "final", "start": m["final_ignition"], "end": round(tl["duration"] + 0.4, 3), "energy": 0.3, "layers": ["drone", "air", "pad"], "chord": "Dmaj9", "level_db": -8, "ramp": 0.05, "breath_before": 0.5},
        ],
        "motifs": [{"t": m["reveal"] + 0.95, "gain": 0.26},
                   {"t": m["breath_elo"][1], "gain": 0.4, "pluck": True},
                   {"t": round(m["cta_at"] + 2.25, 3), "gain": 0.42}],
        "toms": [m["reveal"], m["breath_elo"][1]],
    }


def main(argv: list[str]) -> None:
    tl = json.loads((ROOT / "timeline.json").read_text())
    (ROOT / "tools/music-cue.json").write_text(json.dumps(music_cue(tl), indent=1))
    if "--music-cue-only" in argv:
        return

    # ---- legendas: TRANSCRIPT só com as falas legendadas
    words = []
    for v in tl["vo"]:
        if v["caption"]:
            words += [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in v["words"]]
    cap = (ROOT / "compositions/captions.html").read_text()
    import re
    cap = re.sub(r"var TRANSCRIPT = \[.*?\];", "var TRANSCRIPT = " + json.dumps(words, ensure_ascii=False) + ";", cap, flags=re.S)
    cap = re.sub(r"var KEYWORDS = \[.*?\];", "var KEYWORDS = " + json.dumps(KEYWORDS, ensure_ascii=False) + ";", cap, flags=re.S)
    (ROOT / "compositions/captions.html").write_text(cap)

    # ---- index.html
    jt = {"duration": tl["duration"], "bpm": tl["bpm"], "anchor": tl["anchor"],
          "frames": [{"id": f["id"], "start": f["start"], "end": f["end"]} for f in tl["frames"]],
          "vo": [{"id": v["id"], "start": v["start"], "end": v["end"], "words": v["words"]} for v in tl["vo"]],
          "marks": tl["marks"]}
    hosts = []
    for f in tl["frames"]:
        hosts.append(
            f'      <div id="el-{f["id"][:3]}" data-composition-id="{f["id"]}" data-composition-src="{f["file"]}"\n'
            f'        data-start="{f["start"]}" data-duration="{f["duration"]}" data-track-index="1" data-track-kind="graphics"\n'
            f'        data-width="1920" data-height="1080"></div>')
    audio = []
    for k, v in enumerate(tl["vo"]):
        audio.append(f'      <audio id="vo-{v["id"].lower()}" src="{v["file"]}" data-start="{v["start"]}" '
                     f'data-duration="{v["duration"]}" data-track-index="10" data-audio-group="voiceover" data-volume="1"></audio>')
    # automação de volume (t relativo ao início do som): a cauda da assinatura abre espaço para
    # "Fale. O JARVIS faz." e volta a soar depois da fala
    m = tl["marks"]
    l17 = next(v for v in tl["vo"] if v["id"] == "L17")
    ign = m["final_ignition"]
    # (a faixa de volume SUBSTITUI data-volume, não multiplica: valores absolutos, 0,5 = nível do som)
    auto = {"sfx-final-ignite": [(0.0, 0.5), (round(l17["start"] - ign - 0.3, 3), 0.5),
                                  (round(l17["start"] - ign + 0.05, 3), 0.15), (round(l17["end"] - ign, 3), 0.15),
                                  (round(l17["end"] - ign + 0.6, 3), 0.28)]}
    import html as _html
    # SFX: cada som com a própria duração, em trilhas sem sobreposição (alocação gulosa)
    lanes: list[float] = []
    for name, file, t, vol in sorted(sfx_plan(tl), key=lambda x: x[2]):
        dur = round(flac_duration(ROOT / f"assets/sfx/{file}.flac") + 0.0005, 3)
        lane = next((i for i, end in enumerate(lanes) if end <= t - 0.01), None)
        if lane is None:
            lanes.append(0.0)
            lane = len(lanes) - 1
        lanes[lane] = t + dur
        extra = ""
        if name in auto:
            lane_json = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [{"t": a, "v": b} for a, b in auto[name]]}]})
            extra = f' data-automation="{_html.escape(lane_json)}"'
        audio.append(f'      <audio id="{name}" src="assets/sfx/{file}.flac" data-start="{t}" data-duration="{dur}" '
                     f'data-track-index="{30 + lane}" data-audio-group="sfx" data-volume="{vol}"{extra}></audio>')
    music_path = ROOT / "assets/music/music.flac"
    music = (f'      <audio id="music-bed" src="assets/music/music.flac" data-start="0" data-duration="{tl["duration"]}" '
             f'data-track-index="20" data-audio-group="music" data-volume="0.9"></audio>') if music_path.exists() else ""
    html = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>J.A.R.V.I.S. — filme de apresentação</title>
    <script src="assets/vendor/gsap/gsap.min.js"></script>
    <script src="assets/vendor/gsap/CustomEase.min.js"></script>
    <script src="assets/vendor/gsap/DrawSVGPlugin.min.js"></script>
    <script src="assets/js/jarvis-motion.js"></script>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.JT = {json.dumps(jt, ensure_ascii=False)};
      JT.frame = (id) => JT.frames.find((f) => f.id === id || f.id.startsWith(id));
      JT.v = (id) => JT.vo.find((v) => v.id === id);
      JT.word = (id, text, k = 0) => JT.v(id).words.filter((w) => w.text.toLowerCase().replace(/[.,:;!?]/g, "").startsWith(text.toLowerCase()))[k].start;
      JT.local = (id, t) => t - JT.frame(id).start;
    </script>
    <style>
      @font-face {{ font-family: "Mona Sans"; src: url("assets/fonts/MonaSans-Variable.woff2") format("woff2"); font-weight: 200 900; font-stretch: 75% 125%; }}
      @font-face {{ font-family: "Geist Mono"; src: url("assets/fonts/GeistMono-Variable.woff2") format("woff2"); font-weight: 100 900; }}
      @font-face {{ font-family: "Orbitron"; src: url("assets/fonts/Orbitron-Variable.woff2") format("woff2"); font-weight: 400 900; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #04080c; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #04080c; }}
      #root > div[data-composition-src] {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{tl['duration']}" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
      <div id="el-captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
        data-start="0" data-duration="{tl['duration']}" data-track-index="5" data-track-kind="captions"
        data-width="1920" data-height="1080"></div>
{music}
{chr(10).join(audio)}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(html)
    # carve da trilha sob a narração (refeito sempre: depende dos tempos da voz)
    carve = Path.home() / ".claude/skills/hyperframes-audio/scripts/carve.mjs"
    if music and carve.exists() and "--no-carve" not in argv:
        import subprocess
        r = subprocess.run(["node", str(carve), "--comp", "index.html", "--bed", "music-bed"],
                           cwd=ROOT, capture_output=True, text=True)
        print("carve:", (r.stdout.strip().splitlines() or ["?"])[-1] if r.returncode == 0 else "FALHOU\n" + r.stderr[-800:])
    print(f"index.html: {len(tl['frames'])} cenas, {len(tl['vo'])} falas, {len(sfx_plan(tl))} SFX, "
          f"música {'ok' if music else 'ausente'}, duração {tl['duration']}s")

    # variante sem narração (só com --sem-narracao): mesmo filme sem a voz e sem as legendas (que
    # transcrevem a voz). A trilha mantém o carve, então continua abrindo espaço onde a fala entra.
    # Renderize e apague o arquivo (o lint exige um único index na raiz):
    #   npx hyperframes render -c index-sem-narracao.html -o renders/...; rm index-sem-narracao.html
    if "--sem-narracao" not in argv:
        return
    import re
    silent = (ROOT / "index.html").read_text()
    silent = re.sub(r'\n      <audio id="vo-[^"]+"[^>]*></audio>', "", silent)
    silent = re.sub(r'\n      <div id="el-captions".*?></div>', "", silent, flags=re.S)
    silent = re.sub(r'(<audio id="sfx-final-ignite"[^>]*?) data-automation="[^"]*"', r"\1", silent)  # sem voz, a assinatura soa inteira
    silent = silent.replace("<title>J.A.R.V.I.S. — filme de apresentação</title>",
                            "<title>J.A.R.V.I.S. — filme de apresentação (sem narração)</title>")
    (ROOT / "index-sem-narracao.html").write_text(silent)
    print("index-sem-narracao.html: sem voz e sem legendas")


if __name__ == "__main__":
    main(sys.argv)
