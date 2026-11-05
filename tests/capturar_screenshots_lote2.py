import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE / "tests" / "output_visual" / "lote2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AMOSTRA_LOTE2 = [
    "trabalho/join4/produto/tarefas/README.html",
    "trabalho/join4/produto/tarefas/task-001-etl-piloto-docker-rebuild-guard.html",
    "trabalho/join4/produto/consultas-portal/consultas-portal.html",
    "trabalho/join4/produto/relatorios/status-report-semana-42-2026.html",
    "trabalho/join4/clientes/atlantica/automacoes/dossie-transicao-automacoes-csc-capere-rds.html"
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 1024})

        for rel_path in AMOSTRA_LOTE2:
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
