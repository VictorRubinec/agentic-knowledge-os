---
name: hyperframes
description: Produção de vídeo programático e animações em HTML/CSS/GSAP determinísticos para redes sociais, Shorts, TikTok e YouTube. Use sempre que precisar gerar vídeos, animações ou changelogs visuais por código.
---

# Skill: HyperFrames (Vídeo Programático via HTML/CSS/GSAP)

Esta skill capacita os agentes de IA a criar, editar e compilar vídeos e animações em alta resolução através de código web puro (HTML, Tailwind CSS e GSAP).

---

## 1. Estrutura de Templates

O repositório disponibiliza templates base em `scripts/hyperframes/`:

1. **Vertical (9:16 - 1080x1920)**: `scripts/hyperframes/template-short.html`
   - Otimizado para TikTok, YouTube Shorts e Instagram Reels.
   - Suporta legendas dinâmicas (*kinetic typography*), badges e CTAs.
2. **Horizontal (16:9 - 1920x1080)**: `scripts/hyperframes/template-landscape.html`
   - Otimizado para vídeos explicativos longos no YouTube, demos de produto e changelogs executivos.

---

## 2. Como Gerar ou Modificar Vídeos

1. **Carregar o Template**: Abra o arquivo HTML correspondente e altere os textos nos elementos de ID (`#main-title`, `#description`, `#tagline`).
2. **Ajustar Timings no GSAP**:
   ```javascript
   const tl = gsap.timeline({ paused: false });
   tl.to("#header", { opacity: 1, duration: 0.6 })
     .to("#main-title", { opacity: 1, duration: 0.8 }, "-=0.2");
   ```
3. **Pré-visualização Local**:
   Abra o arquivo HTML no navegador via Playwright CLI:
   ```bash
   playwright-cli open scripts/hyperframes/template-short.html
   ```
4. **Exportação Determinística**:
   O arquivo expõe a função `window.renderFrame(timeInSeconds)` permitindo captura frame a frame via headless browser para compilação em MP4 com FFmpeg.
