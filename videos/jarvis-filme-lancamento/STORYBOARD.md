---
format: 1920x1080
duration: 98s
message: "Fale. O JARVIS faz: o assistente por voz que age de verdade no seu celular Android e no seu PC."
arc: Intriga → Descoberta → Demonstração (clareza + aceleração) → Clímax (capacidade) → Desejo + marca
audience: quem visita o site do JARVIS (pt-BR), curioso por um assistente que age de verdade
mode: autonomous
music: original — Ré menor, pulso eletrônico a 100 BPM, motivo quartal A–D–E–A, resolve em Ré maior no logo
tempo_grid: "100 BPM · tempo forte da ignição em 5,6 s · falas em colcheia, cortes em tempo/compasso"
---

# Storyboard — JARVIS, filme de lançamento

Este vídeo diz a quem visita o site que **o JARVIS não só responde: ele age no seu celular e no seu
PC, com 206 funções, e ainda escreve as próprias ferramentas — sempre sob o seu controle.**
Tempos de fala e marcas vêm de `timeline.json` (gerado por `tools/timeline.py` a partir das falas reais).

| Frame | Beat | Na tela | Por quê |
| --- | --- | --- | --- |
| 01 — Inicialização | gancho · 10,4 s | Escuro, fragmentos reais do app acelerando, log de boot, respiro, ignição do núcleo, J.A.R.V.I.S. | Intriga + product reveal; "E se bastasse falar?" é a promessa em linguagem de resultado |
| 02 — Fale. O JARVIS faz. | promessa · 8,4 s | Corte casado pelo orb para o celular real; título e o que é | O valor chega no 2º beat |
| 03 — Ele age | demonstração · 12,3 s | "Ele não só responde." e 7 verbos no pulso, cada um com seu pictograma | Clareza + aceleração: prova de que age |
| 04 — 206 funções | escala · 9,9 s | Contador 206, 18 áreas reais, cards de função com nível de risco | Tamanho e controle, com os números do produto |
| 05 — Encadeia | demonstração · 12,6 s | Painel "OUVINDO", pedido digitado, cadeia real de 2 funções | Mostra o mecanismo com um exemplo do site |
| 06 — Elo | clímax · 10,2 s | Celular ↔ PC ligados, capacidades do Elo fluindo | Capacidade que diferencia |
| 07 — Ele escreve | clímax · 11,4 s | Código Python se escrevendo, revisão, aprovação, a ferramenta nasce | O momento "como fizeram isso?" + controle |
| 08 — Duas personalidades | clímax · 8,4 s | JARVIS (ciano) × ULTRON (vermelho) em torno de uma memória | Personalidade de marca |
| 09 — Assinatura | desejo + marca · 14,6 s | Respiro, "Feito em português", orb, J.A.R.V.I.S., "Fale. O JARVIS faz.", teste grátis | Assinatura e convite |

## Video direction

- **Ritmo**: 01 lento → 02 médio → 03 rápido (cortes secos nos verbos) → 04–05 médio-rápido →
  respiro (0,9 s) → 06–07 cheio → 08 médio → respiro → 09 lento e silencioso. Momentos "WOW":
  mergulho no orb (01→02), as 206 funções reais como gráfico de unidades que se reorganiza nas 18
  áreas e ganha as cores de risco (04), dados fluindo entre aparelhos com o log das funções reais (06),
  a lacuna no catálogo que vira código, é aprovada e volta como função (07), núcleo final (09).
- **Transições (vocabulário)**: zoom through + corte casado pelo orb (01→02) · corte seco ao preto
  (02→03) · cortes secos no pulso (verbos) · depth push (03→04) · uma unidade vira o card real
  "ligar dispositivo" e a câmera atravessa o card (04→05) · respiro + cortina digital em faixas
  (05→06) · o feixe do Elo vira o cursor que desce para a lacuna do catálogo (06→07) · o catálogo se
  abre ao meio (07→08) · glitch controlado vermelho e corte ao preto (08→09, o único além do flash de
  nome na abertura).
- **Legendas**: faixa inferior, frases quebradas em orações naturais (≤ 44 caracteres), UMA palavra
  em ciano por frase e cada destaque uma vez só no filme (falar, voz, funções, Elo, memória,
  ferramenta, aprova); ocultas quando a tipografia cinética já diz a mesma frase (L02, L04, L05, L08,
  L14, L16, L17, L18).
- **Som**: SFX discretos alinhados a cada entrada; trilha com carve sob a voz; respirações de
  silêncio antes da ignição (5,2–5,6 s), do Elo e do final.

## Frame 1 — Inicialização

- status: built
- src: compositions/frames/01-abertura.html
- duration: 10.4s
- transition_in: cut
- type: hook
- blueprint: logo-assemble-lockup (Adapt)
- focal: núcleo (orb em canvas)
- roles: fragmentos do app = supporting · log de boot = supporting · orb + J.A.R.V.I.S. = hero
- voiceover: "E se bastasse falar?"
- sfx: electric, scan, boot, ticks/cliques por fragmento, riser-long, silêncio, hit-sub-2 + sub-drop, whoosh-soft-3, sweep-up, whoosh-deep
- scene: Escuro, a interface do JARVIS em fragmentos, o núcleo acende e o nome aparece.

Adapt: mantém a assinatura (o logo surge de um ponto de luz e se fecha em lockup); o prelúdio vira
fragmentos reais do app em ritmo acelerando.
Scene 1 (0.0–1.2s): preto quase absoluto; uma linha de varredura ciano acorda o quadro; a voz,
quase sussurrada, pergunta "E se bastasse falar?".
Scene 2 (1.2–4.6s): fragmentos macro da interface real (núcleo, PROCESSANDO, onda de voz, cards de
função com nível de risco, relógio, campo "Diga Hey Jarvis") abrem por fenda em pontos diferentes do
quadro, cada vez mais curtos (0,46 s → 0,08 s); log de boot digitado no canto: INICIALIZANDO NÚCLEO ·
CARREGANDO 206 FUNÇÕES · CONECTANDO ELO · CALIBRANDO VOZ EM PORTUGUÊS · PRONTO.
Scene 3 (4.6–5.6s): tudo apaga; o riser sobe e corta; 0,4 s de silêncio (respiro antes da revelação).
Scene 4 (5.6–8.9s): ignição: um ponto vira esfera com halo, anel orbital tracejado se desenha; o
núcleo sobe e J.A.R.V.I.S. converge letra a letra (tracking + blur→foco), uma varredura de luz.
Scene 5 (8.9–10.4s): o nome sai em blur; a câmera mergulha no núcleo até o quadro virar luz.

## Frame 2 — Fale. O JARVIS faz.

- status: built
- src: compositions/frames/02-promessa.html
- duration: 8.4s
- transition_in: match cut (orb → orb do app)
- type: product_intro
- blueprint: device-surface-showcase (Adapt)
- focal: tela inicial real do app (núcleo + "Diga Hey Jarvis")
- roles: celular = hero · título = supporting · callout = supporting
- voiceover: "Fale. O JARVIS faz. Um assistente pessoal por voz, que controla o seu celular Android e o seu computador."
- sfx: hit-soft no pouso, lock-in, pulse-a no rótulo
- scene: Do núcleo nasce o celular com o app real; a promessa em tipografia grande.

Scene 1 (0.0–1.9s): do centro do núcleo a câmera recua e revela o app real dentro do celular em
profundidade (3/4, leve inclinação).
Scene 2 (0.6–2.8s): "Fale." e "O JARVIS faz." sobem por máscara no terço esquerdo, na batida da voz.
Scene 3 (3.3–8.0s): régua ciano e rótulo mono ASSISTENTE POR VOZ · CELULAR E PC; spotlight breve no
núcleo; callout para o campo "Diga ‘Hey Jarvis’" (acima da faixa de legenda). Legenda da fala L03.

## Frame 3 — Ele age

- status: built
- src: compositions/frames/03-acoes.html
- duration: 12.3s
- transition_in: cut (seco ao preto)
- type: feature_showcase
- blueprint: kinetic-type-beats (Reproduce)
- focal: os verbos
- voiceover: "Ele não só responde. Ele toca na tela. Digita. Abre aplicativos. Liga o computador. Acende a luz. Grava as aulas. E lê o que a câmera vê."
- sfx: um SFX por verbo (toque, teclas, abertura, power, luz, gravação, varredura)
- scene: Tipografia no pulso: cada verbo entra seco com um pictograma de linha.

Scene 1 (0.3–1.9s): "Ele não só responde." centrado, calmo (palavras em cascata).
Scene 2 (2.4–11.6s): corte seco a cada verbo, na entrada exata da voz: TOCA NA TELA (ondulação de
toque) · DIGITA (cursor e teclas) · ABRE APLICATIVOS (grade de apps que se abre) · LIGA O COMPUTADOR
(símbolo de energia + monitor) · ACENDE A LUZ (lâmpada que acende e ilumina o quadro) · GRAVA AS AULAS
(ponto REC + onda) · LÊ O QUE A CÂMERA VÊ (visor com cantoneiras que travam). Cada pictograma se
desenha (draw) e o verbo entra com tracking; alternância esquerda/direita para o olho viajar.
Scene 3 (11.6–12.3s): último verbo recua em profundidade (depth push) para a próxima cena.

## Frame 4 — 206 funções

- status: built
- src: compositions/frames/04-funcoes.html
- duration: 9.9s
- transition_in: depth push
- type: feature_showcase
- blueprint: dataviz-countup + grid-card-assemble (Adapt)
- focal: o número 206
- roles: contador = hero · áreas (18 reais) = supporting · cards de função reais = supporting
- voiceover: "São duzentas e seis funções prontas, em dezoito áreas. Do controle do celular à casa inteligente, cada uma com um nível de risco definido."
- sfx: data-stream no contador, ticks nas áreas, cliques nos níveis de risco
- scene: 206 conta na palavra "duzentas"; as 18 áreas se organizam; cards reais com nível de risco.

Scene 1 (0.6–3.0s): "000" em espera; na palavra "duzentas" o contador vai a 206 e, ao lado, 206
unidades acendem em sincronia (cada quadrado = uma função real do catálogo); luz varre o número;
rótulo FUNÇÕES PRONTAS com tracking.
Scene 2 (3.0–6.9s): em "dezoito", o número recua para o cabeçalho e as unidades voam para as 18 áreas
reais (Celular 43 … Mensagem 2), cada uma com nome e contagem; "controle do celular" destaca Celular,
"casa inteligente" destaca Casa (as outras recuam).
Scene 3 (6.9–8.7s): "nível de risco" — as unidades ganham a cor do nível de cada função (onda da
esquerda para a direita); pílulas 104 SEGURA · 92 MODERADA · 8 SENSÍVEL · 2 CRÍTICA e barra de
distribuição com as cores do site.
Scene 4 (8.7–9.9s): anel de foco na unidade "ligar dispositivo" (Casa); ela sai do quadro como o card
real (nome, pílula MODERADA, descrição do site) e a câmera atravessa o card.

## Frame 5 — Encadeia

- status: built
- src: compositions/frames/05-encadeia.html
- duration: 12.6s
- transition_in: zoom through card
- type: feature_showcase
- blueprint: agent-progress-theater (Adapt)
- focal: painel de pedido (fiel ao "Na prática" do site)
- voiceover: "Você pede. Ele encadeia as ações. — Uma frase, e ele cria a rotina que acende a luz quando você chegar em casa."
- sfx: teclas na digitação, pulse ao ouvir, lock-in em cada passo, confirm no fim
- scene: "OUVINDO", o pedido se escreve, duas funções reais acendem em sequência.

Scene 1 (0.0–3.5s): saímos de dentro do card; "Você pede." (máscara) / "Ele encadeia as ações."
(cascata, "encadeia" em ciano) — a fala é a tipografia.
Scene 2 (3.7–6.3s): painel OUVINDO (rótulo VOCÊ PEDE, barras de voz); o pedido real chega palavra a
palavra com o cursor: “Quando eu chegar em casa, acende a luz da sala.”
Scene 3 (6.6–11.0s): rótulo ELE ENCADEIA, espinha com 01/02; "criar rotina de lugar" acende em "cria"
e "ligar dispositivo" em "acende" (varredura de luz, check desenhado); "ao chegar em casa" fica ciano
em "quando você chegar"; a cadeia respira em "casa".
Scene 4 (11.45–12.6s): o quadro esvazia com desfoque (respiro antes do clímax).

## Frame 6 — Elo

- status: built
- src: compositions/frames/06-elo.html
- duration: 10.2s
- transition_in: digital wipe
- type: feature_showcase
- blueprint: constellation-hub (Adapt)
- focal: a linha do Elo entre celular e PC
- voiceover: "Com o Elo, o celular e o computador funcionam como um só. Ligue a máquina de longe, use a tela dela no celular, e compartilhe arquivos e memória."
- sfx: whoosh-deep na conexão, data-stream contínuo, pulse em cada capacidade
- scene: Celular e PC ligados por um feixe; capacidades reais do Elo fluindo nos dois sentidos.

Scene 1 (0.0–4.0s): cortina digital em faixas (tempo forte do clímax); celular com a tela real do
Elo (lista "ELO (16)") e monitor entram em profundidade; em "Elo" o feixe se desenha; ELO /
16 FUNÇÕES DE ELO; cada aparelho acende no seu nome; pacotes nos dois sentidos em "funcionam como um só".
Scene 2 (4.5–9.5s): log das funções reais na hora da fala — "ligue": → ligar o pc (o PC liga, JARVIS
do PC na tela) · "use": ← controlar pc pelo parsec (a tela do PC aparece no celular) ·
"compartilhe arquivos": → mandar arquivo pro pc / ← pegar arquivo do pc · "memória": ⇄ sincronizar
memória (pulsos se encontram no meio).
Scene 3 (9.5–10.2s): tudo se apaga; o feixe se recolhe num ponto que vira o cursor no centro.

## Frame 7 — Ele escreve

- status: built
- src: compositions/frames/07-ferramenta.html
- duration: 11.4s
- transition_in: linha → cursor
- type: feature_showcase
- blueprint: prompt-type-submit-generate (Adapt)
- focal: painel de código + pílula de estado
- voiceover: "E quando falta uma função, ele escreve a própria ferramenta. Em Python. Mas ela só passa a funcionar depois que você revisa o código e aprova."
- sfx: teclas rápidas no código, scan na revisão, ui-click + confirm na aprovação, lock-in do card
- scene: O código de uma ferramenta nova se escreve; revisão; aprovar; a ferramenta nasce.

Scene 1 (0.0–2.2s): o cursor desce para a lacuna de um catálogo de funções; "falta uma função" = o
contorno tracejado da unidade vazia.
Scene 2 (2.2–4.8s): em "escreve" a câmera entra na lacuna, que se abre no editor (ajustar_receita.py,
PYTHON, ESCRITA PELO JARVIS, pílula PENDENTE); o código Python chega por tokens com o cursor.
Scene 3 (4.8–10.2s): "Python" acende a etiqueta; "só passa a funcionar" pulsa PENDENTE; "revisa" —
faixa de leitura linha a linha; "aprova" — clique em APROVAR, ondulação, pílula vira APROVADA
(texto do rodapé do site: revise o código antes de aprovar).
Scene 4 (10.2–11.4s): o editor se recolhe e a nova função ocupa a lacuna (lock-in); o catálogo se
abre ao meio.

## Frame 8 — Duas personalidades

- status: built
- src: compositions/frames/08-personas.html
- duration: 8.4s
- transition_in: split
- type: benefit_highlight
- blueprint: comparison-split (Adapt)
- focal: dois núcleos (JARVIS ciano, ULTRON vermelho) e a memória compartilhada
- voiceover: "Duas personalidades. Uma só memória. JARVIS ou ULTRON: mesma memória, mesmas ferramentas."
- sfx: sweep-down/sweep-up, pulse duplo, glitch-1 na saída
- scene: Dois núcleos em espelho ligados a um anel de memória comum.

Scene 1 (0.0–3.7s): os dois lados se abrem; cards JARVIS (ciano) e ULTRON (vermelho, cor do botão do
app) entram com inclinações opostas; "Duas personalidades." → "Uma só memória." (máscara) e o nó
MEMÓRIA liga os dois.
Scene 2 (4.2–7.6s): cada card acende no seu nome ("JARVIS", "ULTRON"); "mesma memória" pulsa o nó;
"mesmas ferramentas" liga o nó FERRAMENTAS (texto do catálogo: mesma memória e mesmas ferramentas).
Scene 3 (7.7–8.1s): glitch vermelho controlado (deslocamento cromático, linhas) e corte ao preto.

## Frame 9 — Assinatura

- status: built
- src: compositions/frames/09-final.html
- duration: 14.6s
- transition_in: respiro (preto)
- type: branding + cta
- blueprint: logo-assemble-lockup (Reproduce) + titlecard-reveal
- focal: núcleo + J.A.R.V.I.S.
- voiceover: "Feito em português. No seu celular e no seu computador. — Fale. O JARVIS faz. — Teste grátis por sete dias."
- sfx: silêncio, signature na ignição, shimmer no nome, confirm no convite
- scene: Menos informação, preto/navy, o núcleo acende e assina; convite do teste grátis.

Scene 1 (0.0–0.9s): silêncio visual.
Scene 2 (0.9–5.5s): "Feito em português." (blur→foco, luz varre) e "No seu celular e no seu
computador." em cascata; saída em desfoque; preto.
Scene 3 (6.0–9.4s): ignição suave do núcleo (Ré maior + assinatura sonora), J.A.R.V.I.S. converge;
"Fale. O JARVIS faz." em máscara, na voz.
Scene 4 (9.9–14.6s): pílula "Teste grátis por 7 dias" (texto do site) com varredura de luz; tudo
segura; fade final para o navy.
