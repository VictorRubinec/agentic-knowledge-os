"""Testes unitários e de integração para o Curador de Temas e Scraper do Knowledge OS."""

import datetime
from pathlib import Path
import pytest
import sys

# Garante importação a partir de scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from curador_temas_scraper import (
    classificar_tema,
    calcular_proximo_slot,
    avaliar_relevancia,
    slugify,
    TERMOS_IGNORADOS,
)


def test_slugify():
    assert slugify("Google Gemini 3.8 & Flash Live!") == "google-gemini-38-flash-live"
    assert slugify("Orquestração / Webhooks...") == "orquestraao-webhooks" or "orquestra" in slugify("Orquestração / Webhooks...")


def test_anti_slop_filter():
    item_slop = {
        "titulo": "New Crypto Airdrop Giveaway Meme",
        "raw_text": "Buy this bitcoin token now",
        "engajamento": "⭐ 100 stars"
    }
    assert avaliar_relevancia(item_slop) == 0

    item_valido = {
        "titulo": "Model Context Protocol for Multi-Agent Orchestration",
        "raw_text": "FastMCP server with PostgreSQL pgvector vector search",
        "engajamento": "⭐ 350 stars"
    }
    score = avaliar_relevancia(item_valido)
    assert score >= 50


def test_classificar_tema_rpg():
    cronograma = {}
    item = {
        "titulo": "Grimório de Rituais e Sanidade para Ordem Paranormal RPG",
        "raw_text": "Regras homebrew para o sistema Ordem 2 e cálculo de DT"
    }
    tema_id, dia_nome, dia_chave = classificar_tema(item, cronograma)
    assert tema_id == "rpg"
    assert dia_chave == "saturday"
    assert dia_nome == "Sábado"


def test_classificar_tema_automacoes():
    cronograma = {}
    item = {
        "titulo": "n8n Self-Hosted Webhook Orchestration Pipeline",
        "raw_text": "Automating worker nodes and redis queues for scraping"
    }
    tema_id, dia_nome, dia_chave = classificar_tema(item, cronograma)
    assert tema_id == "automacoes"
    assert dia_chave == "tuesday"


def test_classificar_tema_tendencias_negocios():
    cronograma = {}
    item = {
        "titulo": "AI Reverse Proxy SaaS: B2B Pricing and Token Monetization",
        "raw_text": "Startup revenue models and LLM gateway unit economics"
    }
    tema_id, dia_nome, dia_chave = classificar_tema(item, cronograma)
    assert tema_id == "tendencias_negocios"
    assert dia_chave == "friday"


def test_classificar_tema_evolucao_conhecimento():
    cronograma = {}
    item = {
        "titulo": "PostgreSQL 16 Storage Internals and MVCC Concurrency",
        "raw_text": "Deep systems design and database buffer cache algorithms"
    }
    tema_id, dia_nome, dia_chave = classificar_tema(item, cronograma)
    assert tema_id == "evolucao_conhecimento"
    assert dia_chave == "thursday"


def test_classificar_tema_repositorios_famosos():
    cronograma = {}
    item = {
        "titulo": "awslabs/run-mcp-server",
        "origem": "GitHub Trending",
        "engajamento": "⭐ 1200 stars",
        "raw_text": "Secure container runner for AI MCP tools"
    }
    tema_id, dia_nome, dia_chave = classificar_tema(item, cronograma)
    assert tema_id == "repositorios_famosos"
    assert dia_chave == "wednesday"


def test_classificar_tema_noticias_tech():
    cronograma = {}
    item = {
        "titulo": "Google Announces Next-Gen TPU Hardware for Global Datacenters",
        "origem": "Hacker News",
        "engajamento": "150 pts, 40 comments",
        "raw_text": "Industry releases, hardware updates and cloud ecosystem expansion"
    }
    tema_id, dia_nome, dia_chave = classificar_tema(item, cronograma)
    assert tema_id == "noticias_tech"
    assert dia_chave == "monday"


def test_calcular_proximo_slot_respeita_dia():
    cronograma = {
        "slots_horario": ["08:30", "19:30"]
    }
    fila_tasks = []

    # Procura próximo slot para terça-feira (tuesday = 1)
    slot_iso = calcular_proximo_slot("tuesday", cronograma, fila_tasks)
    dt = datetime.datetime.fromisoformat(slot_iso)

    assert dt.weekday() == 1  # 1 = Terça-feira
    assert f"{dt.hour:02d}:{dt.minute:02d}" in ["08:30", "19:30"]


def test_calcular_proximo_slot_pula_slot_ocupado():
    cronograma = {
        "slots_horario": ["08:30", "19:30"]
    }

    # Simula que o primeiro slot está ocupado
    slot_1 = calcular_proximo_slot("friday", cronograma, [])
    fila_com_ocupado = [{"scheduled_for": slot_1, "status": "pending"}]

    slot_2 = calcular_proximo_slot("friday", cronograma, fila_com_ocupado)
    assert slot_1 != slot_2
    dt1 = datetime.datetime.fromisoformat(slot_1)
    dt2 = datetime.datetime.fromisoformat(slot_2)
    assert dt2.weekday() == 4  # Sexta
