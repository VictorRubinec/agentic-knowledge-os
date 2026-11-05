import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE / "tests" / "output_visual" / "lote3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AMOSTRA_LOTE3 = [
    "trabalho/triade/briefing-estrategico-posicionamento-e-site.html",
    "trabalho/triade/plataforma-interna/Sprints.html",
    "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/proposta-comercial-unificada-somos1.html",
    "trabalho/sites/pessoal/cha-casa-nova/conhecimentos/02-design-system-e-ui-ux.html",
    "trabalho/sites/pessoal/cha-casa-nova/conhecimentos/03-mecanica-lista-presentes-e-pix.html",
    "trabalho/sites/guia-padrao-criacao-sites.html"
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 1024})

        for rel_path in AMOSTRA_LOTE3:
            html_file = WORKSPACE / rel_path
            if not html_file.exists():
                print(f"[PULADO] Arquivo não encontrado: {html_file}")
                continue

            file_url = html_file.resolve().as_uri()
            await page.goto(file_url, wait_until="networkidle")
            await page.wait_for_timeout(1000)

            out_png = OUTPUT_DIR / f"{html_file.stem}.png"
            await page.screenshot(path=str(out_png), full_page=True)
            print(f"[SCREENSHOT] Salvo: {out_png.name}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
