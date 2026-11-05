#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/pesquisa_manager.py — Gerenciador de Pedidos de Pesquisa
Armazena cache de dossiês e orquestra a fila de pesquisas para o ambiente Antigravity.
"""

import re
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict

logger = logging.getLogger("pesquisa_manager")

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent

CACHE_DIR = REPO_ROOT / "projetos" / "pesquisas" / "cache_dossies"
PEDIDOS_DIR = REPO_ROOT / "projetos" / "pesquisas" / "pedidos"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
PEDIDOS_DIR.mkdir(parents=True, exist_ok=True)

FOCOS_MAP = {
    "arq": "🏗️ Arquitetura & Viabilidade Técnica",
    "comp": "📊 Comparativo de Mercado & Alternativas",
    "poc": "💻 Guia Prático & PoC de Teste Local",
    "all": "📚 Deep Dive Completo (360°)"
}

FORMATOS_MAP = {
    "pdf": "📄 Dossiê Knowledge OS (HTML + PDF A4)",
    "resumo": "⚡ Resumo Executivo Rápido (Telegram)"
}


def gerar_slug(texto: str) -> str:
    """Gera um slug amigável e limpo a partir de um nome de tecnologia."""
    slug = re.sub(r'[^a-zA-Z0-9_-]', '', texto.lower().replace(" ", "-")).strip('-')
    return slug[:32] or "tech"


def salvar_dossie_cache(slug: str, dossier, original_url: str) -> Path:
    """
    Salva o dossiê da tecnologia ou coleção em JSON para consulta rápida nos fluxos interativos.
    Quando recebe uma coleção (1:N), salva a coleção e também indexa cada ferramenta individualmente em cache.
    """
    is_col = getattr(dossier, "is_collection", False)
    filepath = CACHE_DIR / f"{slug}.json"

    if is_col and hasattr(dossier, "items"):
        itens_serializados = []
        for it in dossier.items:
            it_slug = gerar_slug(it.tech_name)
            it_data = {
                "slug": it_slug,
                "parent_collection_slug": slug,
                "tech_name": it.tech_name,
                "repo_name": getattr(it, "repo_name", ""),
                "repo_url": getattr(it, "repo_url", ""),
                "repo_found": getattr(it, "repo_found", False),
                "stars_display": getattr(it, "stars_display", ""),
                "stars": getattr(it, "stars", 0),
                "forks": getattr(it, "forks", 0),
                "language": getattr(it, "language", ""),
                "license_name": getattr(it, "license_name", ""),
                "official_website": getattr(it, "official_website", ""),
                "summary": getattr(it, "summary", ""),
                "audio_insights": getattr(it, "audio_insights", ""),
                "video_insights": getattr(it, "video_insights", ""),
                "install_command": getattr(it, "install_command", ""),
                "verdict": getattr(it, "verdict", ""),
                "original_url": original_url,
                "cached_at": datetime.now(timezone.utc).isoformat()
            }
            itens_serializados.append(it_data)
            # Salva também a ferramenta individual em cache para permitir pesquisa avulsa
            item_file = CACHE_DIR / f"{it_slug}.json"
            try:
                with open(item_file, "w", encoding="utf-8") as f:
                    json.dump(it_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Erro ao salvar item individual {it_slug} em cache: {e}")

        col_data = {
            "slug": slug,
            "is_collection": True,
            "collection_title": dossier.collection_title,
            "collection_overview": dossier.collection_overview,
            "tech_name": dossier.collection_title,
            "items": itens_serializados,
            "total_items": len(itens_serializados),
            "original_url": original_url,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(col_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Coleção de tecnologias '{dossier.collection_title}' ({len(itens_serializados)} itens) salva em cache: {filepath.name}")
        return filepath

    # Caso seja ferramenta única
    data = {
        "slug": slug,
        "is_collection": False,
        "tech_name": getattr(dossier, "tech_name", slug),
        "repo_name": getattr(dossier, "repo_name", ""),
        "repo_url": getattr(dossier, "repo_url", ""),
        "repo_found": getattr(dossier, "repo_found", False),
        "stars_display": getattr(dossier, "stars_display", ""),
        "stars": getattr(dossier, "stars", 0),
        "forks": getattr(dossier, "forks", 0),
        "language": getattr(dossier, "language", ""),
        "license_name": getattr(dossier, "license_name", ""),
        "official_website": getattr(dossier, "official_website", ""),
        "summary": getattr(dossier, "summary", ""),
        "audio_insights": getattr(dossier, "audio_insights", ""),
        "video_insights": getattr(dossier, "video_insights", ""),
        "install_command": getattr(dossier, "install_command", ""),
        "verdict": getattr(dossier, "verdict", ""),
        "original_url": original_url,
        "cached_at": datetime.now(timezone.utc).isoformat()
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dossiê da tecnologia '{data['tech_name']}' salvo em cache: {filepath.name}")
    return filepath


def obter_dossie_cache(slug: str) -> dict | None:
    """Recupera o dossiê do disco pelo slug."""
    filepath = CACHE_DIR / f"{slug}.json"
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar dossiê em cache {slug}: {e}")
        return None


def criar_pedido_pesquisa(chat_id: int, slug: str, foco_code: str, formato_code: str, duvida_especifica: str = "") -> dict:
    """
    Cria uma ordem formal de pesquisa técnica e salva em projetos/pesquisas/pedidos/.
    Suporta tanto ferramenta unitária quanto toolkit/coleção de múltiplos repositórios.
    """
    dossie = obter_dossie_cache(slug) or {}
    is_collection = dossie.get("is_collection", False)
    
    if is_collection:
        tech_name = dossie.get("collection_title") or dossie.get("tech_name") or slug.replace("-", " ").title()
        repo_url = ""
    else:
        tech_name = dossie.get("tech_name") or slug.replace("-", " ").title()
        repo_url = dossie.get("repo_url") or dossie.get("official_website") or ""

    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d-%H%M%S")
    pedido_id = f"PESQ-{now.strftime('%Y%m%d')}-{slug[:12]}"

    foco_nome = FOCOS_MAP.get(foco_code, foco_code)
    formato_nome = FORMATOS_MAP.get(formato_code, formato_code)

    pedido_data = {
        "id": pedido_id,
        "chat_id": chat_id,
        "slug": slug,
        "is_collection": is_collection,
        "collection_title": dossie.get("collection_title", ""),
        "collection_overview": dossie.get("collection_overview", ""),
        "items": dossie.get("items", []),
        "tech_name": tech_name,
        "repo_url": repo_url,
        "repo_name": dossie.get("repo_name", ""),
        "stars_display": dossie.get("stars_display", ""),
        "foco_codigo": foco_code,
        "foco_nome": foco_nome,
        "formato_codigo": formato_code,
        "formato_nome": formato_nome,
        "duvida_especifica": duvida_especifica.strip(),
        "summary": dossie.get("summary", ""),
        "install_command": dossie.get("install_command", ""),
        "status": "pendente",
        "criado_em": now.isoformat(),
        "arquivo_saida_html": f"projetos/pesquisas/{slug}/pesquisa-{slug}.html",
        "arquivo_saida_pdf": f"projetos/pesquisas/{slug}/pesquisa-{slug}.pdf"
    }

    filepath = PEDIDOS_DIR / f"{pedido_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(pedido_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Ordem de pesquisa criada com sucesso: {filepath.name}")
    return pedido_data


def listar_pedidos_pendentes() -> list[dict]:
    """Lista todos os pedidos de pesquisa aguardando execução."""
    pedidos = []
    for fp in sorted(PEDIDOS_DIR.glob("PESQ-*.json"), reverse=True):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
                pedidos.append(data)
        except Exception:
            continue
    return pedidos
