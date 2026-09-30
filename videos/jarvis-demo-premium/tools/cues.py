"""Deixas do filme premium (versão completa), ancoradas nas palavras da fala original.

Uso: python tools/cues.py   → data/cues.json (tempos do ORIGINAL; o stage converte para o seu tempo)

Tipos:
  cam      câmera (push/pan) na gravação: s = escala, (x, y) = ponto do original no centro
  chapter  cartela de capítulo (substitui a do original, mesmo texto)
  kin      frase-chave (tipografia cinética) numa região livre da tela
  hud      cartão com linhas que aparecem na palavra
  res      cartão de resultado (o que o produto devolveu)
  call     callout sobre a interface (coordenadas do original)
  boxes    caixas rotuladas sobre regiões da tela (coordenadas do original)
  chip     lembrete fixo que acompanha o filme até disparar
  dia      diagramas: beats4, vector, lock, local, synth, converge, debate
  band     janelas em que a faixa de legenda sai (o produto mostra algo embaixo)
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W = json.loads((ROOT / "data/transcript.json").read_text())


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c for c in s if c.isalnum())


TOK = [norm(x["text"]) for x in W]


def at(phrase: str, after: float = 0.0, end: bool = False) -> float:
    toks = [norm(p) for p in phrase.split()]
    for i in range(len(W) - len(toks) + 1):
        if W[i]["start"] < after:
            continue
        if TOK[i:i + len(toks)] == toks:
            return round(W[i + len(toks) - 1]["end"] if end else W[i]["start"], 3)
    raise KeyError(f"não achei: {phrase!r} depois de {after}")


C: list[dict] = []


def add(k: str, **kw) -> None:
    C.append({"k": k, **kw})


# ------------------------------------------------------------------ 1 · quem eu sou (voz)
add("cam", t=10.4, d=24.0, s=1.07, x=930, y=430, e="sine.inOut")
add("kin", t=at("Eu moro dentro"), d=4.6, pos="R", lines=["Eu moro dentro", "deste computador."], key="computador.")
add("kin", t=at("ninguém vai digitar"), d=3.4, pos="L", lines=["Ninguém vai", "digitar nada."], key="nada.")
add("kin", t=at("se falhar"), d=3.6, pos="R", lines=["Se falhar, você", "vai ver falhar."], key="falhar.")

# ------------------------------------------------------------------ 2 · estado interno (painel)
t_est = at("Estou no ar")
add("cam", t=35.6, d=0.01, s=1.0, x=960, y=540, e="none")
add("cam", t=36.0, d=34.0, s=1.1, x=760, y=470, e="sine.inOut")
add("hud", t=t_est - 0.3, d=at("documentos", t_est, end=True) - t_est + 3.2, x=1235, y=150, w=470, title="ESTADO INTERNO",
    items=[["NO AR", "há 1 minuto", at("no ar", t_est)],
           ["FERRAMENTAS", "245", at("245", t_est)],
           ["CÉREBROS", "Groq · Google", at("Cérebros", t_est)],
           ["MODELO", "openai/gpt-oss-20b", at("Modelo", t_est)],
           ["BUSCA", "DuckDuckGo", at("Busca", t_est)],
           ["VOZ", "Edge", at("Voz por", t_est)],
           ["INTEGRAÇÕES", "Spotify · Agenda Google", at("Integrações", t_est)],
           ["NÃO CONFIGURADAS", "e-mail · casa inteligente", at("Não configuradas", t_est)],
           ["MEMÓRIA", "29 fatos · 4 pessoas · 0 docs", at("Memória:", t_est)]],
    count={"row": 1, "to": 245})

# ------------------------------------------------------------------ 3 · o método
t_ord = at("Eu anuncio")
add("dia", kind="beats4", t=t_ord - 0.4, d=at("sempre.", t_ord, end=True) - t_ord + 1.4,
    steps=[["01", "Anuncio", at("anuncio", t_ord)], ["02", "Faço", at("eu faço", t_ord + 0.5)],
           ["03", "Explico", at("explico", t_ord)], ["04", "Faço de novo, mais fundo", at("E faço de novo", t_ord)]])
add("kin", t=at("Lembrar de você"), d=2.6, pos="R", lines=["Lembrar", "de você."], key="você.")

# ------------------------------------------------------------------ capítulos (cartelas do original, mesmo texto)
CH = [(2, "Memória", "Ele lembra — e lembra do jeito certo", 94.8, 98.8),
      (3, "Navegador", "Ele não lê a internet: ele usa a internet", 192.8, 197.2),
      (4, "Criação", "Imagem feita na hora, não buscada", 306.4, 310.0),
      (5, "Arquivos", "Bagunça entra, ordem sai", 380.0, 383.8),
      (6, "O Conselho", "Ele discute — com ele mesmo", 448.4, 452.2),
      (7, "Som", "Música que toca e sons que não existiam", 532.0, 535.8),
      (8, "Comunicação", "O que eu faço fora desta tela", 629.8, 633.6),
      (9, "Fim", "Obrigado por assistir", 710.4, 713.3)]
for n, title, sub, a, b in CH:
    add("chapter", t0=a, t1=b, n=n, title=title, sub=sub)

# ------------------------------------------------------------------ 4 · guardar e achar (voz)
add("cam", t=99.0, d=40.0, s=1.06, x=930, y=420, e="sine.inOut")
add("kin", t=at("Eu guardo."), d=2.8, pos="R", lines=["Eu guardo."], key="guardo.")
add("res", t=at("Guardei na memória"), d=4.2, pos="R", label="MEMÓRIA · FATO GUARDADO", body="Categoria: geral")
add("res", t=at("vídeo que vai ser publicado"), d=3.4, pos="L", label="BUSCA NA MEMÓRIA", body="“vídeo que vai ser publicado”")
add("res", t=at("Geral: a autodemonstração"), d=7.4, pos="R", label="ENCONTRADO", body="[geral] A autodemonstração do Jarvis foi gravada em 21/09/2026 para ser publicada na internet.")

# ------------------------------------------------------------------ 5 · por dentro: termo × significado
t_vec = at("Uma é a busca clássica")
add("dia", kind="vector", t=at("O que eu guardo vai") - 0.2, d=at("em comum entre as duas", end=True) - at("O que eu guardo vai") + 1.6,
    t_db=at("banco de dados"), t_term=t_vec, t_vec=at("A outra transforma"), t_link=at("É por isso que"))

# ------------------------------------------------------------------ 6 · o lembrete
add("kin", t=at("Exige que eu fale"), d=3.2, pos="R", lines=["Falar sem ninguém", "me chamar."], key="chamar.")
t_rem = at("Lembrete criado")
add("res", t=t_rem, d=4.6, pos="L", label="COMPROMISSO CRIADO", body="Lembrete · hoje às 22:58")
t_fire = 349.6
add("chip", t0=t_rem + 3.8, t1=t_fire, text="LEMBRETE · 22:58", alarm="É AGORA")
add("kin", t=at("Não vai ser edição"), d=3.4, pos="L", lines=["Não vai ser", "edição."], key="edição.")

# ------------------------------------------------------------------ 7 · usar a página (Chromium)
add("kin", t=at("Usar uma página"), d=3.4, pos="R", lines=["Usar uma página", "é que é difícil."], key="difícil.")
add("call", t=217.4, d=1.5, x=420, y=48, lx=640, ly=230, label="CHROMIUM REAL", sub="controlado pelo JARVIS")  # logo depois do corte para o navegador
add("boxes", t=at("Antes de clicar"), d=6.0, grid="wiki-home")
add("cam", t=at("Vou digitar") - 0.4, d=0.9, s=1.35, x=740, y=250, e="power3.inOut")
add("call", t=at("Vou digitar"), d=3.0, x=690, y=132, lx=620, ly=300, label="DIGITANDO", sub="campo de busca")
add("call", t=at("E clicar no botão"), d=2.6, x=1022, y=132, lx=1150, ly=300, label="CLIQUE", sub="Procurar")
add("cam", t=at("E vamos ver") - 0.2, d=1.0, s=1.0, x=960, y=540, e="power3.inOut")

# ------------------------------------------------------------------ 8 · botão eu clico (artigo parado ~1 min → câmera e frases)
add("cam", t=241.0, d=40.0, s=1.16, x=760, y=520, e="sine.inOut")
add("kin", t=at("eu usei o site"), d=3.6, pos="LB", panel=True, lines=["Eu não pedi dados.", "Eu usei o site."], key="site.")
add("kin", t=at("O sistema da sua empresa"), d=3.6, pos="LB", panel=True, lines=["O sistema da empresa,", "o portal da faculdade…"], key=None)
add("kin", t=at("e botão eu clico"), d=3.4, pos="LB", panel=True, lines=["Mas todos têm botão.", "E botão eu clico."], key="clico.")
add("kin", t=at("Só que ler texto"), d=3.6, pos="LB", panel=True, lines=["Ler texto", "não é enxergar."], key="enxergar.")
add("kin", t=at("modelo de visão"), d=2.8, pos="LB", panel=True, lines=["Um modelo", "de visão."], key="visão.")
add("cam", t=285.0, d=1.2, s=1.0, x=960, y=540, e="power3.inOut")

# ------------------------------------------------------------------ 9 · olhos para a tela: as regiões descritas
t_pg = at("A página exibe")
add("boxes", t=t_pg, d=at("barra lateral direita", end=True) - t_pg + 2.2, grid="wiki-article",
    regions=[["CABEÇALHO DE BUSCA", at("cabeçalho", t_pg)], ["MENU LATERAL · SUMÁRIO", at("menu lateral", t_pg)],
             ["TEXTO PRINCIPAL", at("texto principal", t_pg)], ["BARRA LATERAL DIREITA", at("barra lateral direita", t_pg)]])
add("kin", t=at("Essa é a diferença"), d=4.4, pos="R", lines=["O que está escrito", "× o que está na tela."], key="tela.")

# ------------------------------------------------------------------ 10 · a imagem que não existia
add("kin", t=at("Vamos ver se eu consigo"), d=3.6, pos="R", lines=["Útil, até agora.", "Agora, interessante."], key="interessante.")
t_pr = at("Uma figura sozinha")
add("res", t=t_pr, d=at("atrás.", t_pr, end=True) - t_pr + 1.4, pos="R", label="PROMPT · DITO EM VOZ ALTA",
    body="Uma figura sozinha, de costas, diante de uma interface azul enorme, chuva na janela atrás.", typing=True, state="GERANDO")
add("cam", t=333.2, d=14.0, s=1.1, x=960, y=500, e="sine.inOut")
add("kin", t=at("Essa imagem não estava"), d=3.6, pos="L", lines=["Essa imagem não", "estava em lugar nenhum."], key="nenhum.")
add("cam", t=348.6, d=0.8, s=1.0, x=960, y=540, e="power2.inOut")
add("kin", t=at("Criar e encontrar"), d=3.6, pos="L", lines=["Criar ≠ encontrar."], key="encontrar.")
add("band", t0=349.2, t1=363.2)

# ------------------------------------------------------------------ 12 · bagunça → ordem
add("cam", t=392.4, d=0.9, s=1.22, x=1180, y=460, e="power3.inOut")
add("res", t=392.8, d=4.0, pos="TL", label="PASTA DE TESTE", body="10 arquivos · 7 tipos")
add("cam", t=403.8, d=0.8, s=1.0, x=960, y=540, e="power2.inOut")
add("res", t=at("Organizei 10 arquivos"), d=3.6, pos="R", label="ORGANIZADO", body="10 arquivos, por tipo")
add("kin", t=at("Por padrão eu só simulo"), d=4.2, pos="L", lines=["Por padrão,", "eu só simulo."], key="simulo.")
add("kin", t=at("Um PDF."), d=2.4, pos="R", lines=["Um PDF.", "Agora."], key="Agora.")
add("hud", t=at("Word, PowerPoint"), d=4.0, x=1235, y=560, w=470, title="DO MESMO LUGAR",
    items=[["", "Word", at("Word,")], ["", "PowerPoint", at("PowerPoint")], ["", "Excel", at("Excel")]])

# ------------------------------------------------------------------ 13 · o conselho
add("kin", t=at("Eu concordo demais"), d=3.0, pos="R", lines=["Eu concordo", "demais."], key="demais.")
add("kin", t=at("Ele se chama Ultron"), d=3.8, pos="L", lines=["Ele se chama", "ULTRON."], key="ULTRON.", red=True)
add("kin", t=at("a função dele é achar o furo"), d=3.0, pos="R", lines=["Função:", "achar o furo."], key="furo.", red=True)
add("dia", kind="debate", t=at("Vou colocar uma ideia") - 0.2, d=at("Os dois chegaram") - at("Vou colocar uma ideia") + 0.4,
    t_idea=at("Vou colocar uma ideia"), t_same=at("Os dois chegaram"))
add("res", t=at("Os dois chegaram"), d=at("garantida.", end=True) - at("Os dois chegaram") + 1.0, pos="R", label="VEREDITO · JARVIS + ULTRON",
    body="Eu não faria: abandonar a renda fixa antes de ter um único usuário pagante elimina a única fonte de sustento garantida.")
add("kin", t=at("o mesmo motor"), d=3.8, pos="L", lines=["O mesmo motor.", "Personalidades opostas."], key="opostas.")
add("kin", t=at("alguém que ataque"), d=3.8, pos="R", lines=["Alguém que ataque", "antes da realidade."], key="realidade.")

# ------------------------------------------------------------------ 14 · música
add("res", t=at("Tocando a rádio"), d=5.0, pos="R", label="TOCANDO", body="Rádio 101 Smooth Jazz")
add("hud", t=at("Pular, fila"), d=5.0, x=1235, y=520, w=470, title="COM O STREAMING LIGADO",
    items=[["", "Pular · fila · volume", at("Pular, fila")], ["", "Curtir", at("curtir")], ["", "Computador → celular", at("passar a música")]])

# ------------------------------------------------------------------ 15 · sons sintetizados
t_sy = at("Eu sintetizo")
add("dia", kind="synth", t=t_sy - 0.3, d=at("Afinar um deles") - t_sy + 0.2, t_env=at("harmônicos", t_sy),
    t_up=at("Subindo"), t_down=at("Descendo"), t_play=at("São estes"))
add("kin", t=at("Afinar um deles"), d=3.4, pos="R", lines=["Afinar um som é mudar", "um número no código."], key="código.")

# ------------------------------------------------------------------ 16 · comunicação
add("kin", t=at("conversa de quem confia em mim"), d=4.0, pos="R", lines=["Conversa de quem confia", "em mim não vira conteúdo."], key="conteúdo.")
add("res", t=at("Ricardo") - 0.6, d=5.6, pos="L", label="E-MAIL · REDIGIDO PELO JARVIS",
    body="Para: Ricardo · Assunto: a reunião mudou para quinta")

# ------------------------------------------------------------------ 17 · a trava
t_lk = at("Mandar mensagem é ação sensível")
add("dia", kind="lock", t=t_lk - 0.3, d=at("chance de obedecer", end=True) - t_lk + 1.2,
    t_pend=at("Fica pendente"), t_voice=at("em voz alta"), t_code=at("Está numa função"),
    t_buy=at("comprar"), t_move=at("transferir"), t_del=at("apagar", at("transferir")), t_refuse=at("Ela recusa"))

# ------------------------------------------------------------------ 18 · 245 ferramentas convergem
t_cv = at("são 245 ferramentas")
items = [("Memória", "Memória que"), ("Internet de agora", "internet de agora"), ("O computador inteiro", "o computador inteiro"),
         ("Arquivos", "arquivos,"), ("Documentos", "documentos,"), ("Navegador", "um navegador"), ("Olhos para a tela", "olhos para"),
         ("Imagem", "imagem,"), ("Som", "som,"), ("Mensagem", "mensagem,"), ("Travas", "conjunto de travas")]
add("dia", kind="converge", t=t_cv - 0.3, d=at("nem se eu quiser", end=True) - t_cv + 1.0, t_count=at("245", t_cv - 1),
    chips=[[lab, at(ph, t_cv)] for lab, ph in items])

# ------------------------------------------------------------------ 19 · uma máquina só
t_lc = at("Tudo isso roda")
add("dia", kind="local", t=t_lc - 0.2, d=at("para eu pensar", end=True) - t_lc + 1.0, t_data=at("Os dados ficam"), t_text=at("Sai daqui"))
add("kin", t=at("Eu não fui feito"), d=2.4, pos="R", lines=["Não fui feito", "por uma empresa."], key="empresa.")
add("kin", t=at("Eu fui escrito"), d=3.2, pos="R", lines=["Fui escrito por uma", "pessoa, em casa."], key="casa,")
add("kin", t=at("uma função de cada vez"), d=2.6, pos="R", lines=["Uma função", "de cada vez."], key="vez,")

C.sort(key=lambda c: c.get("t", c.get("t0", 0)))
out = {"src_in": 9.95, "src_out": 773.8, "cues": C}
(ROOT / "data/cues.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(len(C), "deixas")
