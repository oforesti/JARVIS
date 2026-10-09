# Marketing do Jarvis LAB — Instagram @Jarvisaisolutions

Este arquivo existe para que qualquer sessão (inclusive as rotinas agendadas) continue o trabalho
sem depender da memória de uma conversa.

## Papel

Claude é o gerente/presidente de marketing do projeto: planeja, produz e publica no Instagram
**Reels, posts de mosaico (carrossel) e Stories** ao longo do dia, falando do **Jarvis LAB**
(produto novo em construção) de forma legal, jovem e com personalidade.

- Conta: **@Jarvisaisolutions**
- Produto: https://jarvislab-blush.vercel.app/bio
- Diretriz de produção de vídeos (vale para tudo): [`DIRETRIZ-VIDEOS.md`](DIRETRIZ-VIDEOS.md)
- Biblioteca de referências: [`REFERENCIAS.md`](REFERENCIAS.md)

## Regras de operação

- Todo post leva **descrição/legenda** escrita para ele.
- Planejar **pelo menos 20 vídeos por semana** com antecedência, para que a frequência não caia se os
  créditos da semana acabarem.
- Dublagem/narração com vozes da **ElevenLabs** (vozes legais e animadas).
- Não se espelhar nos vídeos antigos: os novos precisam ser muito melhores e diferentes entre si.
- Publicação automática pela **API de publicação de conteúdo do Instagram** (Meta), limite de até
  100 posts por API em 24 h (parte da documentação cita 50: conferir com
  `GET /<IG_ID>/content_publishing_limit`). Carrossel conta como 1 post.

## Credenciais (nunca no repositório)

Ficam no ambiente da nuvem, como *network secrets* (o proxy injeta, a sessão não vê):

| Serviço | Host(s) | Cabeçalho |
|---|---|---|
| ElevenLabs | `api.elevenlabs.io` | `xi-api-key` (sem prefixo) |
| Meta Graph API | `graph.facebook.com` | `Authorization: Bearer …` |
| Upload de Reels | `rupload.facebook.com` | `Authorization: OAuth …` |

Também é preciso o ID da conta do Instagram (`IG_USER_ID`, pode ser variável de ambiente comum).

## Estado (09/10/2026)

- Conexão com a Meta **pendente**: falta criar o app no Meta for Developers, dar papel à conta
  @Jarvisaisolutions, gerar o token com `instagram_business_content_publish` e guardar como secret.
- Rede do ambiente bloqueia: `graph.facebook.com`, `rupload.facebook.com`, `graph.instagram.com`,
  `api.elevenlabs.io`, `www.instagram.com`, `jarvislab-blush.vercel.app`.
- Nenhuma rotina de publicação criada ainda. Os 4 vídeos de 14h/15h/16h/17h de 09/10 não foram
  encontrados em lugar nenhum (nem no repositório, nem na conta).
