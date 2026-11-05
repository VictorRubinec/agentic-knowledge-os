import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "tests" / "output_visual" / "lote1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "studio-kustom/README.html",
    "studio-kustom/01-negocio-e-operacao/auditoria-catalogo-shopee-e-produtos.html",
    "studio-kustom/01-negocio-e-operacao/maquinario-insumos-e-fluxo-produtivo.html",
    "studio-kustom/01-negocio-e-operacao/plano-pesquisa-contexto-loja-e-gestao-pedidos.html",
    "studio-kustom/02-engine-e-arquitetura/arquitetura-tecnologica-confiabilidade-shopee.html",
    "studio-kustom/02-engine-e-arquitetura/catalogo-capacidades-studio-kustom-engine.html",
    "studio-kustom/02-engine-e-arquitetura/diretriz-artistica-e-sistema-de-cores.html",
    "studio-kustom/02-engine-e-arquitetura/escopo-mockup-3d-threejs.html",
    "studio-kustom/02-engine-e-arquitetura/especificacao-catalogo-3d-e-correcoes-layout.html",
    "studio-kustom/02-engine-e-arquitetura/planejamento-mestre-studio-kustom-engine-saas.html",
    "studio-kustom/02-engine-e-arquitetura/upscaling-auto-studio-diagnostico-escopo.html",
    "studio-kustom/03-agente-ia-e-governanca/plano-acao-governanca-marcas-e-titulos.html",
    "studio-kustom/03-agente-ia-e-governanca/plano-desenvolvimento-agente-autonomo-engine.html",
    "studio-kustom/03-agente-ia-e-governanca/proposta-projeto-studio-kustom-engine-agente-ia.html"
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
            await page.wait_for_timeout(1500)

            out_png = OUTPUT_DIR / f"{html_path.stem}.png"
            await page.screenshot(path=str(out_png), full_page=True)
            print(f"[SCREENSHOT] Salvo: {out_png.name}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())
