# Filme de apresentação premium do JARVIS — estado e continuidade

Este arquivo existe para que qualquer sessão continue o trabalho sem perder decisões.

## Pedido (resumo do briefing do usuário)

Filme de lançamento premium do JARVIS (padrão de pós-produção ~R$ 10.000) com **HyperFrames +
GSAP**: tecnologia, inteligência, sofisticação, poder e futuro. Regras: não inventar funcionalidades
nem CTA/preço que não estejam no material; efeitos só com função; tipografia cinética só com
palavras ditas; legendas premium com no máximo UMA palavra em ciano; glitch raro; trilha com
ducking; abertura com tensão e revelação; final como assinatura de marca. O usuário **não quer ser
consultado** sobre decisões técnicas de edição — só sobre mudanças de conteúdo/mensagem.

**Mudança de rumo:** o vídeo original (Google Drive, ~600 MB) não pôde ser baixado (o ambiente
bloqueia o Drive; o upload pelo celular para a release falhou). O usuário pediu então: *"faça você o
vídeo de apresentação com as coisas que já fez, baseado no conteúdo do site"* e *"quero narração em
áudio sim"*. O filme atual é, portanto, construído a partir do site (textos, catálogo de funções,
capturas reais do app) com narração neural em pt-BR.

## Estado atual

- Filme completo: 9 cenas, 98,2 s, 1920×1080, 30 fps. `npx hyperframes check` passa sem erros.
- Render final: `renders/jarvis-filme.mp4` (fora do git) → master em `renders/jarvis-filme-master.mp4`.

### Como tudo se encaixa

1. `SCRIPT.md` — roteiro (18 falas, só com o que o site diz).
2. `tools/audio/voice.py` — Kokoro v1.0 (voz `pm_alex`, pt-br) + Parakeet para o tempo de cada
   palavra → `assets/voice/line-*.flac` + `voice.json`. Grafias só para a fala: Djárvis, Últron,
   Páiton, Ândroid. "PC" é mal pronunciado → roteiro usa "computador".
3. `tools/timeline.py` — fonte única de verdade: cenas, falas (na grade de 100 BPM, âncora 5,6 s),
   marcas (`count_start`, `risk_at`, `step1_at`, `elo_wake`, `approve_at`, `final_ignition`…)
   → `timeline.json`. Falas sem legenda quando a tipografia já diz a frase (L02, L04, L05, L08, L14,
   L16, L17, L18).
4. `tools/assemble.py` — gera `index.html` (hosts das cenas, `window.JT` com a linha do tempo,
   legendas, voz, trilha, 86 SFX com duração e trilhas sem sobreposição), reescreve TRANSCRIPT/
   KEYWORDS em `compositions/captions.html`, escreve `tools/music-cue.json` e **reaplica o carve**
   da trilha sob a voz (`carve.mjs`, força 0,8). Sempre rode `python3 tools/assemble.py` depois de
   mudar a linha do tempo.
5. `tools/audio/music.py` — trilha original a partir de `tools/music-cue.json` (Ré menor → Ré maior
   na assinatura, respirações antes das revelações) → `assets/music/music.flac`.
6. `compositions/frames/0N-*.html` — cenas; cada uma lê `JT.frame/JT.word/JT.marks` para sincronizar.
7. `tools/audio/master.py` — mede o render (loudness, pico real, folga voz × trilha por fala),
   leva a −14 LUFS / −1 dBTP e remuxa sem reencodar o vídeo.

### Cenas

01 abertura (fragmentos do app, log, ignição do núcleo, J.A.R.V.I.S., mergulho) · 02 "Fale. O JARVIS
faz." (corte casado orb → app) · 03 sete verbos em cortes secos · 04 206 funções reais em gráfico de
unidades → 18 áreas → cores de risco → card "ligar dispositivo" · 05 pedido → cadeia de 2 funções ·
06 Elo (celular ↔ PC, log de funções reais) · 07 lacuna no catálogo → código Python → revisar →
aprovar → volta ao catálogo · 08 JARVIS/ULTRON, mesma memória e ferramentas · 09 assinatura + "Teste
grátis por 7 dias" (texto do site).

## Ferramentas no container (reinstalar numa sessão nova)

```bash
npm i -g hyperframes@0.8.92 && hyperframes skills update product-launch-video
apt-get install -y ffmpeg
cd videos/jarvis-filme-lancamento && npm i        # @hyperframes/core, exigido pelo carve.mjs
# ASR (HF é bloqueado; mesmo Parakeet pelo GitHub):
curl -L -o p.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2
# TTS: kokoro-multi-lang-v1_0 dos releases tts-models do sherpa-onnx (GitHub)
uv venv audio-venv && VIRTUAL_ENV=$PWD/audio-venv uv pip install numpy scipy soundfile pedalboard pillow numba pyloudnorm matplotlib sherpa-onnx
```

## Aprendizados de lint/check (evitam retrabalho)

- CSS de cada cena é isolado pelo runtime, mas **seletores JS são globais**: sempre prefixar
  (`#fn-…`, `#en-…`, `#lk-…`, `#fe-…`, `#ps-…`, `#fi-…`) e nunca usar `el-` (prefixo dos hosts).
- `fromTo` renderiza o estado inicial na hora: pulsos/flashes que começam visíveis precisam de
  `immediateRender: false` (senão aparecem no quadro 0 da cena).
- Em SVG, escala com GSAP usa `svgOrigin: "x y"` (coordenadas do SVG); `transform-origin` em CSS é
  ignorado/relativo à caixa do elemento.
- `white-space: pre` em contêiner com filhos em linhas separadas renderiza as quebras do HTML.
- Não animar `letterSpacing` (lint): tracking é por caractere (`JM.trackIn`).
- O check de layout enxerga textos mascarados e cenas fora da janela: esconder com `tl.set(…,
  {visibility: "hidden"}, 0)` e marcar proximidade intencional com `data-layout-allow-overlap` no
  próprio elemento de texto.
- Render: `--workers 3` (o automático escolheu 1 worker em 4 núcleos, ~3× mais lento).
