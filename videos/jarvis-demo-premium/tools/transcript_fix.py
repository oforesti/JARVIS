"""Transcrição corrigida do vídeo original (ASR Parakeet + conferência com o texto que o próprio app
mostra na tela). Escreve data/transcript.json: palavras com início/fim e se entram na legenda."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
w = json.load(open(ROOT / "analysis/transcript.json"))

SET = {70: "há", 77: "disponíveis:", 78: "Groq,", 83: "último:", 84: "OpenAI", 85: "GPT-OSS", 86: "20B.",
       91: "DuckDuckGo.", 95: "Edge.", 97: "ativas:", 102: "configuradas:", 103: "e-mail,", 106: "Memória:",
       108: "fatos,", 112: "documentos.", 199: "Categoria:", 204: "por,", 212: "dizer:", 213: "“vídeo",
       217: "publicado”.", 219: "Geral:", 414: "Chromium", 455: "isto:", 580: "exibe", 587: "Homem",
       589: "Ferro,", 593: "cabeçalho", 606: "seções,", 615: "direita.", 658: "existir", 704: "salva",
       739: "se mente", 767: "gero", 803: "São", 805: "arquivos", 815: "Organizei", 817: "arquivos.",
       1146: "Jazz.", 1239: "harmônicos", 1375: "diz: avisa", 1397: "aqui", 1505: "opero"}
DROP = {92, 113, 195, 218, 333, 415, 435, 616, 617, 1147, 1275, 1383}


def find(text, after=0):
    for i in range(after, len(w)):
        if w[i]["text"].lower().strip(".,:;!?") == text:
            return i
    raise KeyError(text)


# trechos sem legenda: a leitura acelerada dos elementos da página e o debate com vozes sobrepostas
HIDE = set(range(463, find("ocultar", 463) + 1)) | set(range(971, 1027))
for i, x in enumerate(w):
    if x["text"].lower().startswith("prompte"):
        SET[i] = "prompts" + x["text"][len("promptes"):]

out = []
for i, x in enumerate(w):
    if i in DROP:
        if out and i - 1 not in DROP:
            out[-1]["end"] = x["end"]
        continue
    out.append({"i": i, "text": SET.get(i, x["text"]), "start": x["start"], "end": x["end"], "caption": i not in HIDE})
(ROOT / "data/transcript.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
print(len(out), "palavras;", sum(1 for o in out if not o["caption"]), "fora da legenda")
