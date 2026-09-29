---
version: 1
name: JARVIS — Launch Film (frame layer)
description: >
  Sistema visual do filme de lançamento do J.A.R.V.I.S. Unidade = o quadro 1920×1080.
  Átomos herdados do produto real (site + app): fundo void/abyss, núcleo luminoso (orb) como
  símbolo, ciano #5cd6f5 como luz e azul elétrico como energia, branco frio e cinza metálico.
  Tipografia do filme: Mona Sans (largura variável 100→125) para voz e títulos, Geist Mono para
  leitura técnica, Orbitron SOMENTE no logotipo "J.A.R.V.I.S." (fonte da marca no app/site).
unit: the frame — 1920×1080 (16:9)
principle: a luz é informação · um acento por vez · a interface real é o herói

colors:
  void: "#04080c"          # fundo universal (site --void)
  abyss: "#08121a"         # plano de profundidade (site --abyss)
  navy: "#061321"          # navy muito escuro, só em glows de fundo
  charcoal: "#0c1117"      # charcoal para painéis opacos
  panel: "#0b1820"         # superfície de UI (site --panel)
  card: "#0f1f29"          # card de UI (site --card)
  line: "#183140"          # hairline (site --line)
  line-hi: "#234656"       # hairline realçada (site --line-hi)
  ice: "#e6f7fd"           # branco frio — títulos (site --ice)
  text: "#c4dae3"          # texto corrido (site --text)
  mist: "#8ea7b2"          # texto secundário / labels (site --mist)
  metal: "#6f8591"         # cinza metálico — réguas, ticks, grids
  cyan: "#5cd6f5"          # ACENTO PRINCIPAL — luz (site --accent)
  cyan-hot: "#a8ecfb"      # núcleo quente do orb (site --orb-mid)
  core: "#f4fdff"          # ponto mais claro do orb
  electric: "#2f7bff"      # azul elétrico — energia, profundidade dos glows
  deep: "#16607c"          # ciano profundo — bordas do orb (site --accent-deep)
  glow-cyan: "rgba(92,214,245,0.22)"
  glow-electric: "rgba(47,123,255,0.16)"
  glass: "rgba(11,24,32,0.58)"
  glass-border: "rgba(92,214,245,0.20)"
  ultron: "#ec5a61"        # SOMENTE se o modo ULTRON aparecer no material

radii:
  pill: "999px"
  card: "18px"
  card-sm: "12px"
  bracket: "0"

typography:
  wordmark:   { fontFamily: "Orbitron", weight: 500, tracking: "0.32em", upper: true, color: "ice", note: "só o logotipo J.A.R.V.I.S." }
  display-xl: { fontFamily: "Mona Sans", stretch: "125%", weight: 300, px: 150, lineHeight: 0.98, tracking: "-0.02em", color: "ice" }
  display-l:  { fontFamily: "Mona Sans", stretch: "125%", weight: 300, px: 112, lineHeight: 1.0, tracking: "-0.015em", color: "ice" }
  word-caps:  { fontFamily: "Mona Sans", stretch: "125%", weight: 600, px: 96, tracking: "0.16em", upper: true, color: "ice" }
  title-m:    { fontFamily: "Mona Sans", stretch: "112%", weight: 500, px: 64, lineHeight: 1.08, tracking: "-0.01em", color: "ice" }
  caption:    { fontFamily: "Mona Sans", stretch: "100%", weight: 500, px: 44, lineHeight: 1.2, tracking: "0", color: "ice", highlight: "cyan" }
  body:       { fontFamily: "Mona Sans", stretch: "100%", weight: 400, px: 32, lineHeight: 1.4, color: "text" }
  hud:        { fontFamily: "Geist Mono", weight: 500, px: 22, tracking: "0.14em", upper: true, color: "mist" }
  hud-strong: { fontFamily: "Geist Mono", weight: 600, px: 26, tracking: "0.12em", upper: true, color: "cyan" }
  numeral:    { fontFamily: "Mona Sans", stretch: "125%", weight: 700, px: 180, tracking: "-0.03em", color: "ice", numeric: "tabular-nums" }

spacing:
  title-safe-x: "192px"    # title-safe 80% (inset 10%): legendas e conteúdo-chave
  title-safe-y: "108px"
  action-safe-x: "96px"    # action-safe 90% (inset 5%): tudo que é visível
  action-safe-y: "54px"
  caption-bottom: "128px"  # base do bloco de legenda até o rodapé (dentro do title-safe)
  grid: "8px"

components:
  orb-core:
    description: >
      O símbolo do JARVIS. Esfera com gradiente radial (core → cyan-hot 26% → cyan 58% → deep 100%),
      halo externo em duas camadas (cyan 50% a 50px, cyan 25% a 160px), anel tracejado orbital
      (stroke cyan 55%, dash 3/6). Respira (escala 1.00↔1.035) — nunca pisca.
  glass-panel:
    backgroundColor: "{colors.glass}"
    border: "1.5px solid {colors.glass-border}"
    rounded: "{radii.card}"
    effects: "backdrop-filter blur(18px) saturate(120%) · highlight interno no topo (1px, ice 10%) · sombra 0 40px 120px rgba(0,0,0,.55)"
    description: "Painel translúcido escuro para UI flutuante e cards de função."
  risk-pill:
    description: "Pílula do produto (SEGURA / MODERADA / SENSÍVEL / CRÍTICA) — fiel ao app: Orbitron 600, tracking .18em, fundo cyan 14%, texto cyan."
  callout:
    description: >
      Linha-guia de 1.5px (cyan 70%) que nasce de um nó (dot 10px com halo) sobre a região real da
      interface e termina num rótulo Geist Mono. A linha se desenha (drawSVG) antes do rótulo entrar.
  spotlight:
    description: >
      Escurecimento do quadro (void a 62%) com máscara radial suave em torno da região que importa;
      entra em 0.5s power2.inOut, sai em 0.35s. Nunca coexistir com mais de um callout.
  hud-bracket:
    description: "Cantoneiras de 28px, 1.5px, metal 70% — enquadram o produto; sem textos piscando."
  caption-bar:
    description: >
      Legenda premium: sem caixa sólida; texto ice sobre um gradiente de leitura (void 0→55%) na base,
      frases curtas (≤ 42 caracteres por linha, máx. 2 linhas), no máximo UMA palavra em cyan por frase.
  light-sweep:
    description: "Faixa de luz diagonal (ice 0→35%→0, 18° de inclinação) que atravessa títulos/UI uma única vez."
---

# JARVIS — Launch Film (frame layer)

## Overview

O filme tem de parecer o lançamento de um produto real, não uma apresentação. O sistema nasce do
próprio JARVIS: o **núcleo luminoso** do app vira o símbolo e a fonte de luz de todo o filme, e a
interface real do produto é tratada como **hero product**. A luz é informação — ela só aparece para
apontar, revelar ou conectar.

- **Fundo**: `void` em todos os quadros, com profundidade dada por glows radiais localizados
  (`navy`/`electric` a baixa intensidade). Nunca gradiente linear de tela cheia (bandas no H.264).
- **Um acento por vez**: `cyan` é a luz; `electric` só dá profundidade ao glow. Texto é `ice`.
- **Contraste de registro tipográfico**: Mona Sans larga (125%) é a voz do JARVIS — frases-chave,
  palavras cinéticas; Mona Sans normal (100%) é a leitura — legendas; Geist Mono é a máquina —
  rótulos técnicos. Orbitron aparece só no logotipo, exatamente como no app.

## The Frame

- **Craft bar**: *Squint* — um elemento domina (um título, um trecho de UI ou o orb).
  *Silence* — nunca mais de três camadas de informação ao mesmo tempo.
  *Restraint* — glow ≤ 0.45 de opacidade de pico; glitch no máximo duas vezes no filme.
  *Reference* — filmes de lançamento de hardware/software premium (Apple, Nothing, Tesla);
  a falha parece "vídeo de IA": neon por todo lado, partículas aleatórias, HUD barulhento.
- **Safe areas** (padrão Premiere/Studio): action-safe 90% (inset 96×54px) para tudo que é
  visível; title-safe 80% (inset 192×108px) para legendas e conteúdo-chave. Legenda com base a
  128px do rodapé.
- **Profundidade em três planos**: fundo (void + glow + grid técnico a 8–12%), plano médio (o
  produto / a mensagem), primeiro plano (callouts, rótulos mono, cantoneiras).

## Colors

`void` é o chão universal. `ice` para títulos, `text` para leitura, `mist`/`metal` para metadados e
estruturas. `cyan` é o único acento de cor saturada em texto; `electric` só existe como luz difusa.
`ultron` é reservado: só entra se o material mostrar o modo ULTRON — nunca como decoração.

## Typography

- Palavras cinéticas em caixa alta, Mona Sans 125% peso 600, tracking 0.16em — **no máximo uma
  palavra por vez**, e só palavras que a narração diz ou a imagem demonstra.
- Frases-chave: Mona Sans 125% peso 300 com a palavra de peso 700–800 (contraste extremo 300↔800).
- Legendas: Mona Sans 100% peso 500, 44px, até 2 linhas, destaque de uma palavra em `cyan`.
- Mono: Geist Mono 500, caixa alta, tracking 0.14em, 22–26px.
- Tracking de display −0.02em; nada abaixo de 22px na tela.

## Motion (vocabulário)

- **Entradas**: `expo.out` (confiança), `power3.out` (UI), `power4.out` (aterrissagem de câmera).
  **Saídas**: `power2.in` / `power3.in`, sempre mais rápidas que a entrada.
- **Tipografia**: mask reveal (linha sobe de dentro de uma máscara), tracking expansion
  (0.02em→0.16em com blur 12px→0), blur-to-focus, light sweep único, width expansion (100%→125%).
- **Câmera digital**: push-in lento (1.00→1.06 em 4–6 s, `sine.inOut`), punch-in controlado em UI
  (≤1.35× com contra-translação), parallax de 2–3 planos.
- **Transições (vocabulário)**: corte seco (ritmo) · match cut pelo orb · zoom through interface ·
  depth push (cena recua em Z com blur) · light sweep wipe · máscara por painel de UI · digital wipe
  com linha de varredura · glitch controlado (máx. 2×, 4–6 frames).
- **Proibido**: `repeat: -1`, piscar texto, partículas aleatórias, elastic/bounce em tipografia.

## Sound (identidade)

Sub grave para peso, pulsos digitais para interface, whooshes macios para deslocamento, cliques
de UI curtos e secos, riser apenas antes das revelações, e uma assinatura sonora curta para o logo
(tríade suave + sub + cauda de reverb longa). Tudo abaixo da voz: a narração é soberana.
