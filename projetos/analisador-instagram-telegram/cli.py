#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/cli.py — Interface de Linha de Comando para Teste Direto
"""

import sys
import argparse
import logging

# Configuração de encoding para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import validar_configuracoes
from downloader import baixar_reel_instagram, extrair_url_instagram
from analyzer import analisar_video_multimodal
from researcher import enriquecer_e_validar_tecnologia

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cli_analyzer")


def formatar_dossie_terminal(dossier, post) -> str:
    """Formata o dossiê para exibição rica no terminal."""
    linhas = [
        "=" * 70,
        "🔍 TECNOLOGIA IDENTIFICADA",
        f"  • Nome: {dossier.tech_name}",
    ]
    if dossier.repo_found:
        linhas.extend([
            f"  • Repositório: {dossier.repo_url}",
            f"  • Métricas: {dossier.stars_display} stars | {dossier.forks} forks | Linguagem: {dossier.language}",
            f"  • Licença: {dossier.license_name} | Atualizado: {dossier.last_update_str}",
        ])
    if dossier.official_website:
        linhas.append(f"  • Site / Docs: {dossier.official_website}")

    linhas.extend([
        "",
        "💡 O QUE É E O QUE RESOLVE",
        f"  {dossier.summary}",
        "",
        "📺 DESTAQUES DA PERCEPÇÃO TRIPLA",
        f"  • Áudio (Fala): {dossier.audio_insights}",
        f"  • Vídeo (Tela/Código): {dossier.video_insights}",
    ])

    if dossier.install_command:
        linhas.extend([
            "",
            "⚙️ COMANDO DE INSTALAÇÃO / EXECUÇÃO",
            f"  {dossier.install_command}",
        ])

    linhas.extend([
        "",
        "⚖️ VEREDITO TÉCNICO",
        f"  {dossier.verdict}",
        "=" * 70,
    ])

    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(description="Analisador Multimodal de Reels do Instagram & Repositórios")
    parser.add_argument("url", help="URL do Instagram Reel ou Post a ser analisado")
    args = parser.parse_args()

    # Valida configurações mínimas (Gemini API)
    ok, msg = validar_configuracoes(precisa_telegram=False)
    if not ok:
        print(f"❌ Erro de Configuração:\n{msg}")
        sys.exit(1)

    url_alvo = extrair_url_instagram(args.url) or args.url
    print(f"\n🚀 Iniciando análise do Reel: {url_alvo}\n")

    post = None
    try:
        print("⏳ 1/3 Baixando vídeo MP4 e metadados com yt-dlp...")
        post = baixar_reel_instagram(url_alvo)
        print(f"   ✔ Mídia baixada: {post.video_path.name} ({post.video_path.stat().st_size / 1024 / 1024:.1f} MB)")
        if post.caption:
            print(f"   ✔ Legenda extraída: {len(post.caption)} caracteres")

        print("\n⏳ 2/3 Processando áudio, vídeo e legenda com Gemini 2.5 Flash...")
        analise = analisar_video_multimodal(post)
        print(f"   ✔ Tecnologia identificada: {analise.tech_name}")

        print("\n⏳ 3/3 Auditando no GitHub e cruzando métricas...")
        dossie = enriquecer_e_validar_tecnologia(analise, post.caption)

        print("\n" + formatar_dossie_terminal(dossie, post))

    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        sys.exit(1)

    finally:
        if post:
            post.cleanup()


if __name__ == "__main__":
    main()
