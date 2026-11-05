#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/config.py — Centralizador de Configurações
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent

# Carregar .env local do projeto e da raiz se existirem
load_dotenv(BASE_DIR / ".env")
load_dotenv(REPO_ROOT / ".env")

# Carregar credenciais legadas do telegram_config.json se disponíveis
telegram_json_path = REPO_ROOT / "scripts" / "telegram_config.json"
legacy_cfg = {}
if telegram_json_path.exists():
    try:
        with open(telegram_json_path, "r", encoding="utf-8") as f:
            legacy_cfg = json.load(f)
    except Exception:
        pass

# Resolução com fallback inteligente
TELEGRAM_BOT_TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN")
    or legacy_cfg.get("TELEGRAM_BOT_TOKEN")
    or ""
)

TELEGRAM_ALLOWED_USER_ID = str(
    os.getenv("TELEGRAM_ALLOWED_USER_ID")
    or legacy_cfg.get("TELEGRAM_ALLOWED_USER_ID")
    or ""
)

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or legacy_cfg.get("GEMINI_API_KEY")
    or legacy_cfg.get("GOOGLE_API_KEY")
    or ""
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Diretório para armazenamento temporário de vídeos
TEMP_MEDIA_DIR = BASE_DIR / "temp_media"
TEMP_MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def validar_configuracoes(precisa_telegram: bool = True) -> tuple[bool, str]:
    """Valida se as chaves essenciais estão configuradas."""
    erros = []
    if precisa_telegram and not TELEGRAM_BOT_TOKEN:
        erros.append("TELEGRAM_BOT_TOKEN não configurado. Defina no .env ou em scripts/telegram_config.json.")
    if not GEMINI_API_KEY:
        erros.append("GEMINI_API_KEY não configurada. Obtenha em https://aistudio.google.com/ e defina no .env.")

    if erros:
        return False, "\n".join(erros)
    return True, "Configurações válidas."
