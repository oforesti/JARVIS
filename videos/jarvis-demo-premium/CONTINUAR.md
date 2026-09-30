# Como continuar — JARVIS, demonstração premium (recut do vídeo original)

Entregas: **versão completa** (~13 min, a demonstração inteira, em ordem) e **trailer** (~90–120 s).
Fonte: vídeo original do Drive (`assets/source/original.mp4`, 541 MB — fora do git; baixar de novo
para `assets/source/` e extrair `original-audio.flac` com ffmpeg se o contêiner for novo).

## Pipeline da versão completa

```bash
npm i                                   # @hyperframes/core (carve precisa)
python3 tools/transcript_fix.py         # analysis/transcript.json → data/transcript.json (correções + trechos ocultos)
python3 tools/cues.py                   # deixas visuais → data/cues.json (tempo do original)
python3 tools/build.py --no-carve       # index.html + tools/music-cue.json (sem trilha ainda)
cd tools/audio && <venv-audio>/bin/python music_long.py ../music-cue.json ../../assets/audio/music.flac && cd ../..
python3 tools/build.py                  # de novo, agora com a trilha e o carve (ducking sob a voz)
npx hyperframes lint && npx hyperframes check
npx hyperframes render --quality delivery --fps 30 --workers 3 -o renders/jarvis-demo-completo.mp4
python3 tools/audio/master.py ...       # −14 LUFS / −1 dBTP, remux AAC 320k (ver --help)
```

- `assets/audio/music.flac` (107 MB) fica fora do git: é determinística, sai de `music_long.py`.
- Mapa de tempo: filme = original + 3,05 s (`STAGE_AT 13.0 − SRC_IN 9.95`). Deixas em `cues.py` usam o tempo do original.
- `compositions/stage.html` é o motor: câmera, frases (kin), HUDs, cartões, callouts, diagramas e cartelas a partir de `window.CUES`.
- A faixa inferior (`#sg-band`) cobre a transcrição ao vivo do próprio app e a marca d'água do Windows; ela sai só no lembrete (349,2–363,2 s do original), quando a legenda sobe.

## Lições

- `fromTo` renderiza o "from" na hora: flashes, pulsos e linhas de varredura com `immediateRender: false`.
- Texto escondido só por máscara ainda conta no layout do `check` → `autoAlpha: 0` fora da janela.
- Frases seguidas no mesmo lado dividem o mesmo fundo (encadeamento) para não piscar.
- Automação de volume substitui `data-volume` (valores absolutos). Carve precisa de `@hyperframes/core`.
- Só um `index.html` com `data-composition-id` na raiz do projeto: o trailer mora em `trailer/`.
- Nunca `pkill -f` com um padrão que apareça no próprio comando.
