"""Etapa 1 — análise completa do vídeo original.

Uso: python analyze.py <video> <saida-dir>

Gera em <saida-dir>:
  probe.json            metadados (ffprobe)
  scenes.json           instantes de corte detectados (mudança de cena)
  silences.json         pausas na fala (silencedetect)
  loudness.json         loudness de curto prazo (1 s) ao longo do vídeo
  frames/ttt.t.jpg      1 quadro a cada `--every` segundos (padrão 1.0)
  sheets/sheet-NN.jpg   contact sheets 5×4 com o tempo gravado em cada quadro
  audio.wav             áudio 48 kHz estéreo (para transcrição e mix)
  transcript.json       palavras com início/fim (Parakeet, pt)
  report.md             resumo legível: duração, cortes, pausas, falas por trecho
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def probe(video: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(video)])
    return json.loads(out.stdout)


def scenes(video: Path, threshold: float = 0.22) -> list[dict]:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf",
                        f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"],
                       text=True, capture_output=True)
    res = []
    for m in re.finditer(r"pts_time:([0-9.]+).*?scene_score=?([0-9.]+)?", p.stderr):
        res.append({"t": round(float(m.group(1)), 3)})
    if not res:  # showinfo não traz o score; extrai só os tempos
        res = [{"t": round(float(t), 3)} for t in re.findall(r"pts_time:([0-9.]+)", p.stderr)]
    return res


def silences(audio: Path, noise_db: int = -38, min_d: float = 0.3) -> list[dict]:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(audio), "-af",
                        f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"],
                       text=True, capture_output=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", p.stderr)]
    ends = re.findall(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", p.stderr)
    out = []
    for i, s in enumerate(starts):
        if i < len(ends):
            out.append({"start": round(s, 3), "end": round(float(ends[i][0]), 3), "dur": round(float(ends[i][1]), 3)})
        else:
            out.append({"start": round(s, 3), "end": None, "dur": None})
    return out


def loudness(audio: Path) -> list[dict]:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(audio), "-af",
                        "ebur128=framelog=verbose", "-f", "null", "-"], text=True, capture_output=True)
    out = []
    for m in re.finditer(r"t:\s*([0-9.]+)\s+TARGET.*?M:\s*(-?[0-9.]+|-inf)\s+S:\s*(-?[0-9.]+|-inf)", p.stderr):
        t = float(m.group(1))
        if abs(t - round(t)) < 0.051:
            s = m.group(3)
            out.append({"t": round(t), "short_lufs": None if s == "-inf" else float(s)})
    return out


def frames_and_sheets(video: Path, out: Path, duration: float, every: float = 1.0) -> list[Path]:
    fdir = out / "frames"
    sdir = out / "sheets"
    shutil.rmtree(fdir, ignore_errors=True)
    shutil.rmtree(sdir, ignore_errors=True)
    fdir.mkdir(parents=True)
    sdir.mkdir(parents=True)
    # quadros com timestamp gravado (drawtext sem arquivo de fonte → usa fonte padrão do fontconfig)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
         f"fps=1/{every},scale=480:-2,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6",
         str(fdir / "f%05d.jpg")])
    files = sorted(fdir.glob("f*.jpg"))
    per = 20
    sheets = []
    for i in range(0, len(files), per):
        chunk = files[i:i + per]
        lst = out / "sheets" / f"list-{i // per:02d}.txt"
        lst.write_text("".join(f"file '{f.resolve()}'\n" for f in chunk))
        sheet = sdir / f"sheet-{i // per:02d}.jpg"
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
             "tile=5x4:padding=4:margin=4:color=0x202020", "-frames:v", "1", str(sheet)])
        lst.unlink()
        sheets.append(sheet)
    return sheets


def transcribe(audio: Path, out: Path) -> list[dict]:
    work = out / "asr"
    work.mkdir(exist_ok=True)
    shutil.copy(audio, work / "audio.wav")
    subprocess.run(["hyperframes", "transcribe", "audio.wav", "--engine", "parakeet", "--language", "pt", "--json"],
                   cwd=work, check=True, text=True, capture_output=True, timeout=3600)
    words = json.loads((work / "transcript.json").read_text())
    (out / "transcript.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
    return words


def report(out: Path, pr: dict, sc: list, si: list, words: list, lu: list) -> None:
    fmt = pr["format"]
    dur = float(fmt["duration"])
    lines = ["# Análise do vídeo original", ""]
    for s in pr["streams"]:
        if s["codec_type"] == "video":
            lines.append(f"- Vídeo: {s['width']}×{s['height']} · {s.get('codec_name')} · {s.get('r_frame_rate')} fps · {s.get('pix_fmt')}")
        if s["codec_type"] == "audio":
            lines.append(f"- Áudio: {s.get('codec_name')} · {s.get('sample_rate')} Hz · {s.get('channels')} ch")
    lines.append(f"- Duração: {dur:.2f} s ({int(dur // 60)}:{dur % 60:05.2f})")
    lines.append(f"- Cortes detectados: {len(sc)}")
    lines.append(f"- Pausas ≥ 0,3 s: {len(si)} (total {sum((x['dur'] or 0) for x in si):.1f} s)")
    lines.append(f"- Palavras transcritas: {len(words)}")
    lines += ["", "## Fala por trecho (quebras em pausas > 0,6 s)", ""]
    cur, t0 = [], None
    for i, w in enumerate(words):
        if t0 is None:
            t0 = w["start"]
        cur.append(w["text"])
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None or nxt["start"] - w["end"] > 0.6:
            lines.append(f"- `{t0:7.2f}–{w['end']:7.2f}` {' '.join(cur)}")
            cur, t0 = [], None
    lines += ["", "## Cortes", "", ", ".join(f"{x['t']:.2f}" for x in sc) or "—"]
    lines += ["", "## Pausas", ""]
    lines += [f"- {x['start']:.2f}–{x['end']:.2f} ({x['dur']:.2f} s)" for x in si if x["end"]]
    (out / "report.md").write_text("\n".join(lines) + "\n")


def main(argv: list[str]) -> None:
    video = Path(argv[1]).resolve()
    out = Path(argv[2]).resolve()
    every = float(argv[argv.index("--every") + 1]) if "--every" in argv else 1.0
    out.mkdir(parents=True, exist_ok=True)
    pr = probe(video)
    (out / "probe.json").write_text(json.dumps(pr, indent=1))
    dur = float(pr["format"]["duration"])
    audio = out / "audio.wav"
    has_audio = any(s["codec_type"] == "audio" for s in pr["streams"])
    if has_audio:
        run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "2", "-ar", "48000", str(audio)])
    sc = scenes(video)
    (out / "scenes.json").write_text(json.dumps(sc, indent=1))
    si = silences(audio) if has_audio else []
    (out / "silences.json").write_text(json.dumps(si, indent=1))
    lu = loudness(audio) if has_audio else []
    (out / "loudness.json").write_text(json.dumps(lu, indent=1))
    sheets = frames_and_sheets(video, out, dur, every)
    words = transcribe(audio, out) if has_audio else []
    report(out, pr, sc, si, words, lu)
    print(json.dumps({"duration": dur, "scenes": len(sc), "silences": len(si), "words": len(words),
                      "sheets": [str(s) for s in sheets]}, indent=1))


if __name__ == "__main__":
    main(sys.argv)
