import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

WORKSPACE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE / "tests" / "output_visual" / "lote4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AMOSTRA_LOTE4 = [
    "projetos/knowledge-os-v2/README.html",
    "projetos/darkcraft-engine/conhecimentos/01-arquitetura-e-pipeline.html",
    "projetos/gerador-fichas-ordem-2/conhecimentos/01-anatomia-visual-e-posicionamento-a4.html",
    "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/fundamentos-de-ia-e-llms.html",
    "00-meta/GUIA_STACK_TECNOLOGICA_RECOMENDADA.html",
    "projetos/monitor-uptime-status.html"
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        for rel_path in AMOSTRA_LOTE4:
            file_path = WORKSPACE / rel_path
            if not file_path.exists():
                print(f"[AVISO] Arquivo não encontrado: {file_path}")
                continue

            file_url = file_path.as_uri()
            page.goto(file_url, wait_until="networkidle")
            page.wait_for_timeout(1000)

            out_name = file_path.stem + ".png"
            out_file = OUTPUT_DIR / out_name
            page.screenshot(path=str(out_file), full_page=True)
            print(f"[SCREENSHOT] Salvo: {out_name}")

        browser.close()

if __name__ == "__main__":
    main()
