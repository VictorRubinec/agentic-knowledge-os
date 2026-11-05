#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/validar_anti_slop.py
Linter estático de conformidade visual e técnica Anti-Slop / Ponytail para o Knowledge OS.
Garante sobriedade, elimina estética genérica de IA e prioriza padrões nativos da web.
"""

import sys
import os
import re
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent

# Padrões proibidos (AI Slop)
SLOP_PATTERNS = [
    {
        "id": "AI_SPARKLE_EMOJI",
        "regex": re.compile(r'(?:<h[1-6][^>]*>|#{1,6}\s+)[^<#\n]*[✨🌟🔮🤖][^<#\n]*', re.IGNORECASE),
        "msg": "Uso de emojis de 'brilho mágico' ou IA (✨, 🌟, 🔮, 🤖) em títulos/cabeçalhos de seção."
    },
    {
        "id": "PURPLE_AI_GRADIENT",
        "regex": re.compile(r'linear-gradient\([^)]*(?:#6366f1|#a855f7|#8b5cf6|#ec4899)[^)]*(?:#a855f7|#ec4899|#3b82f6)[^)]*\)', re.IGNORECASE),
        "msg": "Gradiente roxo/índigo/rosa genérico de IA detectado no estilo inline ou CSS."
    },
    {
        "id": "FAKE_AI_BADGE",
        "regex": re.compile(r'<span[^>]*badge[^>]*>\s*(?:AI[- ]POWERED|MAGIC|SMART AI|BETA PRO)\s*</span>', re.IGNORECASE),
        "msg": "Badge decorativo de 'AI-Powered' ou 'Magic' sem correspondência semântica real."
    },
    {
        "id": "DECORATIVE_TERMINAL_SLOP",
        "regex": re.compile(r'<div[^>]*terminal-header[^>]*>.*(?:red|yellow|green).*</div>', re.IGNORECASE | re.DOTALL),
        "msg": "Falso cabeçalho de terminal decorativo com botões de janela simulados."
    }
]

def validar_arquivo(caminho: Path) -> list[dict]:
    """Varre um arquivo específico e retorna lista de violações encontradas."""
    violacoes = []
    try:
        conteudo = caminho.read_text(encoding="utf-8")
    except Exception as e:
        return [{"linha": 0, "id": "FILE_READ_ERROR", "msg": f"Erro ao ler arquivo: {e}"}]

    linhas = conteudo.splitlines()

    # Checagem linha a linha
    for num_linha, linha in enumerate(linhas, start=1):
        for pattern in SLOP_PATTERNS:
            if pattern["id"] == "DECORATIVE_TERMINAL_SLOP":
                continue # checado no bloco completo
            if pattern["regex"].search(linha):
                violacoes.append({
                    "linha": num_linha,
                    "id": pattern["id"],
                    "msg": pattern["msg"],
                    "trecho": linha.strip()[:80]
                })

    # Checagem multiline
    for pattern in SLOP_PATTERNS:
        if pattern["id"] == "DECORATIVE_TERMINAL_SLOP":
            if pattern["regex"].search(conteudo):
                violacoes.append({
                    "linha": 1,
                    "id": pattern["id"],
                    "msg": pattern["msg"],
                    "trecho": "Bloco de falso terminal detectado no documento."
                })

    return violacoes

def escanear_repositorio() -> tuple[int, int, int]:
    """Escanear todos os arquivos HTML e MD do repositório."""
    total_arquivos = 0
    arquivos_com_erro = 0
    total_violacoes = 0

    pastas_alvo = ["projetos", "trabalho", "00-meta"]
    for pasta in pastas_alvo:
        p = WORKSPACE_DIR / pasta
        if not p.exists():
            continue
        for ext in ("*.html", "*.md", "*.mdx"):
            for arquivo in p.rglob(ext):
                # Pula arquivos de terceiros ou caches
                if any(ignored in arquivo.parts for ignored in ("node_modules", ".gemini", "dist", "build", "temp_media")):
                    continue
                total_arquivos += 1
                violacoes = validar_arquivo(arquivo)
                if violacoes:
                    arquivos_com_erro += 1
                    total_violacoes += len(violacoes)
                    rel_path = arquivo.relative_to(WORKSPACE_DIR)
                    print(f"\n[FALHA] {rel_path} ({len(violacoes)} infração/ões):")
                    for v in violacoes:
                        print(f"  - L{v['linha']}: [{v['id']}] {v['msg']}")
                        if "trecho" in v and v["trecho"]:
                            print(f"    Trecho: \"{v['trecho']}\"")

    return total_arquivos, arquivos_com_erro, total_violacoes

def main():
    parser = argparse.ArgumentParser(description="Linter Anti-Slop para o Knowledge OS")
    parser.add_argument("--file", "-f", help="Caminho de um arquivo específico a ser validado")
    parser.add_argument("--scan", "-s", action="store_true", help="Escanear todos os documentos do repositório")

    args = parser.parse_args()

    if args.file:
        caminho = Path(args.file)
        if not caminho.is_absolute():
            caminho = WORKSPACE_DIR / caminho
        if not caminho.exists():
            print(f"[ERRO] Arquivo não encontrado: {caminho}")
            sys.exit(1)

        violacoes = validar_arquivo(caminho)
        if violacoes:
            print(f"[FALHA] Foram encontradas {len(violacoes)} violações Anti-Slop no arquivo {caminho.name}:")
            for v in violacoes:
                print(f"  - L{v['linha']}: [{v['id']}] {v['msg']}")
                if "trecho" in v:
                    print(f"    Trecho: \"{v['trecho']}\"")
            sys.exit(1)
        else:
            print(f"[SUCESSO] Arquivo {caminho.name} está 100% conforme às regras Anti-Slop.")
            sys.exit(0)

    elif args.scan:
        print("Iniciando varredura Anti-Slop no Knowledge OS...")
        total, errados, violacoes = escanear_repositorio()
        print("\n" + "=" * 60)
        print(f"Resumo: {total} arquivos escaneados, {errados} com infrações, {violacoes} violações totais.")
        print("=" * 60)
        sys.exit(1 if violacoes > 0 else 0)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
