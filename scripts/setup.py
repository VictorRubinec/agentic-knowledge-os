#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI de Setup e Boas-Vindas do Agentic Knowledge OS
Inicializa o ambiente, verifica dependÃªncias e personaliza o AGENTS.md.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=" * 70)
    print("  ðŸš€ BEM-VINDO AO AGENTIC KNOWLEDGE OS")
    print("  Second Brain de Alta Performance para Agentes de IA AutÃ´nomos")
    print("=" * 70)
    print()

    # Pergunta nome do usuÃ¡rio
    user_name = input("ðŸ‘‰ Qual Ã© o seu nome ou empresa para personalizar o ambiente? (Enter para padrÃ£o): ").strip()
    if not user_name:
        user_name = "Desenvolvedor"

    agents_md = ROOT / "AGENTS.md"
    if agents_md.exists():
        content = agents_md.read_text(encoding="utf-8")
        content = content.replace("VocÃª Ã© o **Agente de AnotaÃ§Ãµes Pessoal**.", f"VocÃª Ã© o **Agente de Engenharia e Conhecimento de {user_name}**.")
        agents_md.write_text(content, encoding="utf-8")
        print(f"âœ… AGENTS.md personalizado para '{user_name}'!")

    print()
    instalar = input("ðŸ“¦ Deseja instalar as dependÃªncias agora (Playwright, Node, Python)? [S/n]: ").strip().lower()
    if instalar != 'n':
        print("
â³ Instalando dependÃªncias Python...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=False)

        print("
â³ Instalando Playwright Chromium...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)

        if (ROOT / "package.json").exists():
            print("
â³ Instalando dependÃªncias Node...")
            subprocess.run(["npm", "install"], cwd=str(ROOT), shell=True, check=False)

    print()
    print("=" * 70)
    print("ðŸŽ‰ AMBIENTE CONFIGURADO COM SUCESSO!")
    print("Experimente compilar um PDF de teste executando:")
    print("  python scripts/gerar_pdf.py exemplos/01-ata-reuniao-arquitetura.mdx")
    print("=" * 70)

if __name__ == "__main__":
    main()
