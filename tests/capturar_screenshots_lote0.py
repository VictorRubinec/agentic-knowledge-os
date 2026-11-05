import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "tests" / "output_visual"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "starter-kit/exemplos/01-ata-reuniao-arquitetura.html",
    "starter-kit/exemplos/02-tarefa-autenticacao-jwt.html",
    "00-meta/TEMPLATE_TAREFA.html",
    "00-meta/TEMPLATE_NOTA.html",
    "00-meta/TEMPLATE_PROJETO_TRIADE.html"
]

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        for rel in FILES:
            html_path = (WORKSPACE_DIR / rel).resolve()
            if not html_path.exists():
                print(f"[SKIP] Não encontrado: {rel}")
                continue

            file_url = f"file:///{html_path.as_posix()}"
            await page.goto(file_url, wait_until="networkidle")
            # Aguarda renderização de Mermaid e scripts
            await page.wait_for_timeout(1500)

            out_png = OUTPUT_DIR / f"{html_path.stem}.png"
            await page.screenshot(path=str(out_png), full_page=True)
            print(f"[SCREENSHOT] Salvo: {out_png.name}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())
