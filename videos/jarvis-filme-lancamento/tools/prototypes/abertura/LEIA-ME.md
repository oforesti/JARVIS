# Protótipo da abertura (animática)

Feito antes de o vídeo original estar disponível, com as capturas do app que estão no site
(`assets/app-*.jpg`). Serve de referência de direção para a abertura do filme:

- fragmentos de interface em ritmo acelerando (0,46 s → 0,08 s) com log de inicialização;
- respiro de silêncio antes da revelação;
- ignição do núcleo (orb em canvas, nítido em qualquer escala) e revelação de J.A.R.V.I.S.;
- mergulho no orb e *match cut* para o orb real do app, com recuo de câmera revelando a interface.

Para rodar: copie `assets/fonts`, `assets/vendor`, `assets/js` e `assets/sfx` do projeto para
`assets/` aqui, gere a trilha com `python ../../audio/music.py music-cue.json assets/music` e
converta `assets/music/music.wav` para FLAC; depois `npx hyperframes preview`.
