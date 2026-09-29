/*
 * JARVIS — vocabulário de movimento do filme.
 * Todas as funções recebem a timeline pausada da cena e um tempo absoluto (s)
 * nessa timeline. Tudo é fromTo/set explícito: seguro para seek em qualquer
 * direção, determinístico, sem relógio e sem aleatoriedade.
 */
(function () {
  const E = {
    enter: "expo.out",        // chegada confiante
    ui: "power3.out",         // UI e cards
    land: "power4.out",       // aterrissagem de câmera
    move: "power2.inOut",     // deslocamento entre posições
    exit: "power2.in",        // saída que acelera
    exitHard: "power3.in",
    breathe: "sine.inOut",
  };

  // PRNG com semente (para detalhes pseudo-aleatórios determinísticos)
  function rng(seed) {
    let s = seed >>> 0 || 1;
    return function () {
      s ^= s << 13; s >>>= 0;
      s ^= s >> 17;
      s ^= s << 5; s >>>= 0;
      return (s >>> 0) / 4294967296;
    };
  }

  // Divide o texto de um elemento em spans por caractere (preserva espaços).
  function splitChars(el) {
    if (el.dataset.split === "chars") return Array.from(el.querySelectorAll(".jm-ch"));
    const text = el.textContent;
    el.textContent = "";
    const out = [];
    for (const ch of text) {
      const s = document.createElement("span");
      s.className = "jm-ch";
      s.textContent = ch === " " ? " " : ch;
      s.style.display = "inline-block";
      el.appendChild(s);
      out.push(s);
    }
    el.dataset.split = "chars";
    return out;
  }

  function splitWords(el) {
    if (el.dataset.split === "words") return Array.from(el.querySelectorAll(".jm-w"));
    const words = el.textContent.trim().split(/\s+/);
    el.textContent = "";
    const out = [];
    words.forEach((w, i) => {
      const s = document.createElement("span");
      s.className = "jm-w";
      s.textContent = w;
      s.style.display = "inline-block";
      el.appendChild(s);
      if (i < words.length - 1) el.appendChild(document.createTextNode(" "));
      out.push(s);
    });
    el.dataset.split = "words";
    return out;
  }

  // ---------------------------------------------------------------- tipografia
  // Linha sobe de dentro de uma máscara (o pai precisa de overflow:hidden).
  function maskReveal(tl, lines, at, o = {}) {
    const { dur = 0.95, stagger = 0.09, ease = E.enter, from = 108 } = o;
    [].concat(lines).forEach((el, i) => {
      tl.fromTo(el, { yPercent: from }, { yPercent: 0, duration: dur, ease }, at + i * stagger);
    });
    return at + dur + stagger * ([].concat(lines).length - 1);
  }

  // Tracking: caracteres convergem do espaçamento largo para o natural, com blur→foco.
  function trackIn(tl, el, at, o = {}) {
    const { spread = 0.22, dur = 1.15, blur = 12, ease = E.enter, stagger = 0.028, fontPx = 96 } = o;
    const chars = splitChars(el);
    const mid = (chars.length - 1) / 2;
    chars.forEach((c, i) => {
      const d = (i - mid) * spread * fontPx;
      tl.fromTo(c, { x: d, opacity: 0, filter: `blur(${blur}px)` },
        { x: 0, opacity: 1, filter: "blur(0px)", duration: dur, ease }, at + Math.abs(i - mid) * stagger);
    });
    return at + dur + mid * stagger;
  }

  // Expansão de tracking na saída: letras se afastam e desfocam.
  function trackOut(tl, el, at, o = {}) {
    const { spread = 0.12, dur = 0.55, blur = 10, ease = E.exit, fontPx = 96 } = o;
    const chars = splitChars(el);
    const mid = (chars.length - 1) / 2;
    chars.forEach((c, i) => {
      const d = (i - mid) * spread * fontPx;
      tl.fromTo(c, { x: 0, opacity: 1, filter: "blur(0px)" },
        { x: d, opacity: 0, filter: `blur(${blur}px)`, duration: dur, ease, immediateRender: false }, at);
    });
    return at + dur;
  }

  // Blur→foco com leve escala (títulos, frases-chave).
  function focusIn(tl, el, at, o = {}) {
    const { dur = 1.0, blur = 16, scale = 1.045, ease = E.ui } = o;
    tl.fromTo(el, { opacity: 0, scale, filter: `blur(${blur}px)` },
      { opacity: 1, scale: 1, filter: "blur(0px)", duration: dur, ease }, at);
    return at + dur;
  }

  function focusOut(tl, el, at, o = {}) {
    const { dur = 0.45, blur = 10, scale = 0.985, ease = E.exit } = o;
    tl.fromTo(el, { opacity: 1, scale: 1, filter: "blur(0px)" },
      { opacity: 0, scale, filter: `blur(${blur}px)`, duration: dur, ease, immediateRender: false }, at);
    return at + dur;
  }

  // Palavras entram em cascata (sobem + blur curto).
  function wordsIn(tl, el, at, o = {}) {
    const { dur = 0.6, y = 22, blur = 8, stagger = 0.06, ease = E.ui } = o;
    const words = splitWords(el);
    words.forEach((w, i) => {
      tl.fromTo(w, { y, opacity: 0, filter: `blur(${blur}px)` },
        { y: 0, opacity: 1, filter: "blur(0px)", duration: dur, ease }, at + i * stagger);
    });
    return at + dur + stagger * (words.length - 1);
  }

  // Varredura de luz única sobre texto com background-clip:text (classe .jm-shine).
  function shine(tl, el, at, o = {}) {
    const { dur = 1.3, ease = E.move } = o;
    tl.fromTo(el, { backgroundPosition: "120% 0%" }, { backgroundPosition: "-20% 0%", duration: dur, ease }, at);
    return at + dur;
  }

  // Régua/traço que se desenha a partir de uma origem.
  function drawLine(tl, el, at, o = {}) {
    const { dur = 0.8, origin = "left center", ease = E.enter, axis = "x" } = o;
    const from = axis === "x" ? { scaleX: 0 } : { scaleY: 0 };
    const to = axis === "x" ? { scaleX: 1 } : { scaleY: 1 };
    tl.fromTo(el, { ...from, transformOrigin: origin, opacity: 1 }, { ...to, duration: dur, ease }, at);
    return at + dur;
  }

  // Contador determinístico (tabular nums no CSS).
  function countUp(tl, el, at, from, to, o = {}) {
    const { dur = 1.4, ease = "power2.out", fmt = (v) => String(Math.round(v)) } = o;
    const proxy = { v: from };
    el.textContent = fmt(from);
    tl.fromTo(proxy, { v: from }, {
      v: to, duration: dur, ease,
      onUpdate: () => { el.textContent = fmt(proxy.v); },
    }, at);
    return at + dur;
  }

  // Rótulo mono de HUD: entra deslizando curto, sem piscar.
  function hudIn(tl, el, at, o = {}) {
    const { dur = 0.55, x = -14, ease = E.ui } = o;
    tl.fromTo(el, { opacity: 0, x }, { opacity: 1, x: 0, duration: dur, ease }, at);
    return at + dur;
  }

  function fadeOut(tl, els, at, o = {}) {
    const { dur = 0.3, y = 0, ease = E.exit } = o;
    tl.fromTo(els, { opacity: 1, y: 0 }, { opacity: 0, y, duration: dur, ease, immediateRender: false }, at);
    return at + dur;
  }

  // Respiração finita (sem repeat infinito): n ciclos de ida e volta.
  function breathe(tl, el, at, until, o = {}) {
    const { period = 3.2, scale = 1.03, opacity = null } = o;
    const cycles = Math.max(1, Math.floor((until - at) / period));
    const to = { scale, duration: period / 2, ease: E.breathe, yoyo: true, repeat: cycles * 2 - 1 };
    if (opacity !== null) to.opacity = opacity;
    tl.to(el, to, at);
  }

  // ---------------------------------------------------------------- o núcleo (orb)
  // Desenhado em canvas a cada atualização: nítido em qualquer tamanho (sem emendas de tile).
  // Estado: {x, y, r, alpha, halo, bloom, spec, ring, ringDraw, ringRot, flash}
  function drawOrb(ctx, s) {
    const W = ctx.canvas.width, H = ctx.canvas.height;
    ctx.clearRect(0, 0, W, H);
    const a = s.alpha == null ? 1 : s.alpha;
    if (a <= 0.001) return;
    const { x, y, r } = s;
    const k = r / 110;
    ctx.save();
    ctx.globalAlpha = a;
    // halo externo (azul elétrico no limite, ciano perto do núcleo)
    if (s.halo > 0) {
      const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3.6);
      g.addColorStop(0, `rgba(92,214,245,${0.30 * s.halo})`);
      g.addColorStop(0.55, `rgba(47,123,255,${0.10 * s.halo})`);
      g.addColorStop(1, "rgba(47,123,255,0)");
      ctx.fillStyle = g;
      ctx.fillRect(x - r * 3.6, y - r * 3.6, r * 7.2, r * 7.2);
    }
    if (s.bloom > 0) {
      const g = ctx.createRadialGradient(x, y, r * 0.6, x, y, r * 1.85);
      g.addColorStop(0, `rgba(168,236,251,${0.55 * s.bloom})`);
      g.addColorStop(0.6, `rgba(92,214,245,${0.14 * s.bloom})`);
      g.addColorStop(1, "rgba(92,214,245,0)");
      ctx.fillStyle = g;
      ctx.fillRect(x - r * 1.85, y - r * 1.85, r * 3.7, r * 3.7);
    }
    // anel orbital tracejado (o do favicon), desenhado progressivamente
    if (s.ring > 0 && s.ringDraw > 0) {
      const R = r * 1.87;
      const start = -Math.PI / 2 + (s.ringRot || 0) * Math.PI / 180;
      const end = start + Math.PI * 2 * Math.min(1, s.ringDraw);
      ctx.save();
      ctx.strokeStyle = `rgba(92,214,245,${0.55 * s.ring})`;
      ctx.lineWidth = Math.max(1, 1.5 * Math.min(k, 3));
      ctx.setLineDash([3 * Math.min(k, 4), 7 * Math.min(k, 4)]);
      ctx.beginPath();
      ctx.arc(x, y, R, start, end);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = `rgba(168,236,251,${0.95 * s.ring})`;
      ctx.beginPath();
      ctx.arc(x + Math.cos(end) * R, y + Math.sin(end) * R, 3.5 * Math.min(k, 3), 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    // esfera
    ctx.save();
    ctx.shadowColor = "rgba(92,214,245,0.5)";
    ctx.shadowBlur = 50 * Math.min(k, 6);
    const sg = ctx.createRadialGradient(x - r * 0.28, y - r * 0.40, 0, x, y, r * 1.02);
    sg.addColorStop(0, "#f4fdff");
    sg.addColorStop(0.26, "#a8ecfb");
    sg.addColorStop(0.58, "#5cd6f5");
    sg.addColorStop(1, "#16607c");
    ctx.fillStyle = sg;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    // terminador (sombra interna suave embaixo-direita)
    const tg = ctx.createRadialGradient(x - r * 0.22, y - r * 0.28, r * 0.35, x, y, r);
    tg.addColorStop(0, "rgba(8,40,60,0)");
    tg.addColorStop(0.78, "rgba(8,40,60,0)");
    tg.addColorStop(1, "rgba(8,40,60,0.42)");
    ctx.fillStyle = tg;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    // brilho especular
    if (s.spec > 0) {
      const hg = ctx.createRadialGradient(x - r * 0.34, y - r * 0.46, 0, x - r * 0.34, y - r * 0.46, r * 0.5);
      hg.addColorStop(0, `rgba(255,255,255,${0.85 * s.spec})`);
      hg.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = hg;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
    // clarão de ignição (luz aditiva, nunca névoa cinza)
    if (s.flash > 0) {
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      const fg = ctx.createRadialGradient(x, y, 0, x, y, Math.max(W, H) * 0.55);
      fg.addColorStop(0, `rgba(168,236,251,${0.55 * s.flash})`);
      fg.addColorStop(0.25, `rgba(92,214,245,${0.22 * s.flash})`);
      fg.addColorStop(1, "rgba(47,123,255,0)");
      ctx.fillStyle = fg;
      ctx.fillRect(0, 0, W, H);
      ctx.restore();
    }
  }

  // Cria o estado do orb ligado a um canvas; os tweens mexem no estado e redesenham.
  function orbRig(canvas, init) {
    const ctx = canvas.getContext("2d");
    const s = Object.assign({ x: 960, y: 540, r: 110, alpha: 1, halo: 1, bloom: 1, spec: 1, ring: 1, ringDraw: 1, ringRot: 0, flash: 0 }, init || {});
    const draw = () => drawOrb(ctx, s);
    draw();
    return {
      s, draw,
      // tween seguro para seek: fromTo explícito no estado + redesenho
      to(tl, from, to, at, dur, ease) {
        tl.fromTo(s, from, Object.assign({}, to, { duration: dur, ease, onUpdate: draw, immediateRender: false }), at);
      },
    };
  }

  window.JM = { E, rng, splitChars, splitWords, maskReveal, trackIn, trackOut, focusIn, focusOut,
    wordsIn, shine, drawLine, countUp, hudIn, fadeOut, breathe, drawOrb, orbRig };
})();
