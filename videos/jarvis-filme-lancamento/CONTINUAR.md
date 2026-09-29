# Filme de apresentação premium do JARVIS — estado e continuidade

Este arquivo existe para que qualquer sessão continue o trabalho sem perder decisões.

## Pedido (resumo do briefing do usuário)

Transformar o vídeo original de apresentação do JARVIS num **filme de lançamento premium**
(padrão de pós-produção ~R$ 10.000) usando **HyperFrames + GSAP**: analisar o vídeo inteiro antes
de editar (transcrição com timestamps, beats), storyboard por beat, sistema visual, plano de
motion/texto/transições/som, construir, preview, revisar frames, corrigir e renderizar.
Regras: não inventar funcionalidades nem CTA/preço que não estejam no material; efeitos só com
função (atenção, explicação, impacto, ritmo, tecnologia, conexão); tipografia cinética só com
palavras ditas/demonstradas; legendas premium com no máximo UMA palavra em ciano; glitch raro;
trilha com ducking; abertura com tensão e product reveal; final como assinatura de marca.
O usuário **não quer ser consultado** sobre decisões técnicas de edição — só sobre mudanças de
conteúdo/mensagem. Ele pediu explicitamente o render final (Etapa 9).

## Onde está o vídeo original

- Google Drive: `https://drive.google.com/file/d/1P5gGDxjceHSofwyn9THCVHQYqnRENoxd/view`
  (mesmo link do site). ~600 MB. **O ambiente cloud padrão (Trusted) bloqueia o Google Drive.**
- Alternativa: release `video_original` em `oforesti/JARVIS` (estava publicada **sem** o arquivo).
- Para baixar do Drive com a rede liberada:
  `curl -L -o original.mp4 "https://drive.usercontent.google.com/download?id=1P5gGDxjceHSofwyn9THCVHQYqnRENoxd&export=download&confirm=t"`
- Não commitar o vídeo (600 MB). Guardar fora do git (`analysis/` e `assets/source/` estão no .gitignore
  ou devem ser adicionados).

## Estado atual (pronto e validado)

- Projeto HyperFrames 0.8.92 em `videos/jarvis-filme-lancamento` (rota `/general-video`,
  modo autônomo com storyboard interno). GSAP 3.15 e fontes **locais** (`assets/vendor`,
  `assets/fonts`) — o ambiente bloqueia jsdelivr/unpkg.
- `frame.md`: sistema visual (paleta real do app/site, Mona Sans larga/normal + Geist Mono;
  Orbitron só no logotipo J.A.R.V.I.S., como no produto). Safe areas title/action.
- `assets/js/jarvis-motion.js`: vocabulário de movimento (maskReveal, trackIn/Out, focusIn/Out,
  wordsIn, shine, drawLine, countUp, hudIn, breathe) e **orb em canvas** (`JM.orbRig`), que
  resolve emendas de tile ao ampliar gradientes no Chrome.
- `compositions/captions.html`: trilha única de legendas (`var TRANSCRIPT`, `KEYWORDS`,
  `BREAK_AFTER`, `HIDDEN_GROUPS`), troca seca entre frases coladas, hard-kill na saída,
  destaque ciano sincronizado à palavra falada, sombra de leitura só com legenda.
- `tools/analyze.py`: Etapa 1 automática (probe, cortes, pausas, loudness, frames, contact
  sheets 5×4 com timecode, transcrição Parakeet pt, `report.md`).
- `tools/audio/`: `dsp.py` (síntese, filtros, reverb por convolução, **limitador próprio** —
  o Limiter do pedalboard aplica ganho oculto, não usar), `sfx.py` (33 SFX → `assets/sfx/*.flac`),
  `music.py` (trilha original por cue map: Ré menor → Ré maior no logo, motivo A–D–E–A,
  envelope macro por seção e respirações antes das revelações).
- `tools/prototypes/abertura/`: animática da abertura (fragmentos de UI acelerando, log de
  inicialização, silêncio, ignição do núcleo, J.A.R.V.I.S., mergulho no orb e match cut para o
  orb do app). Usa capturas do site — na versão final os fragmentos vêm do vídeo.

## Ferramentas no container (reinstalar numa sessão nova)

```bash
npm i -g hyperframes@0.8.92
hyperframes skills update general-video
apt-get install -y ffmpeg
# transcrição: modelos do HF são bloqueados; o mesmo Parakeet (hashes idênticos) vem do GitHub:
curl -L -o p.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2
tar xjf p.tar.bz2 && mkdir -p ~/.cache/hyperframes/parakeet/parakeet-tdt-0.6b-v3-int8 && \
  mv sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/{encoder,decoder,joiner}.int8.onnx sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/tokens.txt ~/.cache/hyperframes/parakeet/parakeet-tdt-0.6b-v3-int8/
hyperframes models install parakeet
uv venv audio-venv && VIRTUAL_ENV=$PWD/audio-venv uv pip install numpy scipy soundfile pedalboard pillow numba pyloudnorm matplotlib
```

Separação de voz (se o original tiver música sob a narração): modelos UVR MDX-Net em
`github.com/TRvlvr/model_repo/releases` (acessível); Demucs (fbaipublicfiles) é bloqueado.

## Aprendizados de lint/check (evitam retrabalho)

- Cada sub-composição que usa uma fonte precisa do próprio `@font-face` (url `assets/fonts/...`).
- Camadas: produto → escurecimento/spotlight → tipografia/callouts → legendas. Nenhum texto
  gráfico na faixa de legenda (y > 820) enquanto houver legenda.
- Decorativos (grids, brilhos, sombras de leitura) com `data-layout-ignore`; sobreposição
  intencional de texto com `data-layout-allow-occlusion` no próprio elemento de texto.
- Parakeet adianta ~0,2 s a primeira palavra após silêncio: encaixar no fim da pausa detectada.
- Render local: ~4–5× o tempo real (beginframe, 2 workers).

## Próximos passos

1. Baixar o vídeo e rodar `python tools/analyze.py <video> analysis/` (Etapa 1).
2. Ver contact sheets + `report.md`; escrever `STORYBOARD.md` por beat (Etapas 2–4).
3. Construir as cenas como sub-composições + trilha de legendas + áudio (Etapa 5).
4. `hyperframes check`, snapshots por cena, animation map, correções (Etapas 6–8).
5. Render `--quality delivery`, verificar com ffprobe, commit e push (Etapa 9).
