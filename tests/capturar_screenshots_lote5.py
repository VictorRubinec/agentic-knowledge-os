import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

WORKSPACE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE / "tests" / "output_visual" / "lote5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AMOSTRA_LOTE5 = [
    "rpg/sistemas/ordem-2/exemplos/exemplo.html",
    "rpg/mesas/estacao-monte-calvario/ato-00-prologo.html",
    "rpg/mesas/estacao-monte-calvario/ato-04-transmissao-da-verdade.html",
    "rpg/mesas/estacao-monte-calvario/resumo-da-mesa.html",
    "rpg/sistemas/ordem-paranormal/habilidades/rituais.html",
    "rpg/sistemas/ordem-paranormal/itens-e-equipamentos/armas-e-modificacoes.html",
    "rpg/sistemas/ordem-2/criacao-personagem/ocupacoes.html",
    "rpg/mesas/ordem-2-playtest/ato-1/a-maldicao-do-idolo-de-pedra-ato-1.html"
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        for rel_path in AMOSTRA_LOTE5:
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
