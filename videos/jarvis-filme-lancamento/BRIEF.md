---
workflow: product-launch-video
flow: automation
storyboard: yes
mode: autonomous
message: "Fale. O JARVIS faz: o assistente por voz que age de verdade no seu celular Android e no seu PC."
destination: site (seção Apresentação) e YouTube
aspect: 1920x1080
language: pt-BR
length: ~85-90s
angle: lançamento de produto (vender), a partir do conteúdo do site
narration: yes
vo_mode: roteiro escrito a partir do site, sem inventar funcionalidades
voice: neural pt-BR local (Kokoro/Piper) — ElevenLabs/HeyGen/Microsoft bloqueados no ambiente
music: trilha original composta por código (tools/audio/music.py)
style_preset: bespoke (frame.md do produto)
---

# Brief

## Intent

Filme de lançamento premium do J.A.R.V.I.S. (padrão de pós-produção ~R$ 10.000), feito a partir
do **conteúdo do site** porque o vídeo original (Google Drive, ~600 MB) não pôde ser acessado
deste ambiente. O espectador deve pensar: "Que produto é esse?", "Como fizeram isso?",
"Eu quero experimentar." Tecnologia + inteligência + sofisticação + poder + futuro.

Arco: intriga → descoberta → demonstração (clareza + aceleração) → clímax (capacidade e impacto)
→ final (desejo + marca). Respirações antes das grandes revelações.

## Customizations (do briefing original do usuário)

- Identidade: preto profundo / charcoal / navy, azul elétrico e ciano; branco frio e cinza metálico;
  glows controlados; nada de neon excessivo, partículas aleatórias, robôs, cérebros digitais.
- Efeitos só com função; sofisticação > quantidade. Glitch no máximo 2×.
- Interface do produto como hero product (spotlight, callouts, profundidade, parallax).
- Tipografia cinética só com palavras ditas/demonstradas; entradas: mask reveal, tracking
  expansion, blur-to-focus, light sweep, wipe.
- Legendas premium sincronizadas com a fala, frases curtas, no máximo UMA palavra em ciano.
- Vocabulário de transições variado (match cut, zoom through interface, depth, light sweep,
  máscara, digital wipe, glitch raro).
- Sound design sincronizado e trilha cinematográfica com ducking sob a voz.
- Abertura: tela escura, fragmentos da interface, tensão, então o reveal de J.A.R.V.I.S.
- Final: reduzir informação, voltar ao preto/navy, símbolo/nome surgindo, som de assinatura.
- Não inventar CTA, preço ou promessa: CTA usado é o do site ("Teste grátis por 7 dias").
- Usuário pediu **narração em áudio** (mensagem de 29/09) e o render final.

## Assets

- `capture/extracted/catalog.json`: catálogo real do site (206 funções, 18 áreas, riscos,
  exemplos de pedidos e cadeias de funções, integrações).
- Capturas reais do app no site (4 telas do celular: núcleo/Hey Jarvis, Celular, Elo, Estudo).
- Símbolo: o núcleo luminoso (orb) do favicon/app; logotipo J.A.R.V.I.S. em Orbitron (como no app).

## Notes

- O usuário não quer ser consultado sobre decisões técnicas de edição; só sobre mudanças
  de conteúdo/mensagem.
