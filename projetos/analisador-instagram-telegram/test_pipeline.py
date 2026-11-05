#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para o pipeline do Analisador de Reels & Bot Telegram.
"""

import pytest
from downloader import extrair_url_instagram
from researcher import formatar_stars, formatar_data_relativa


def test_extrair_url_instagram():
    """Testa a extração correta de URLs de Reels e Posts em diferentes formatos."""
    # Formato Reel clássico
    url1 = "https://www.instagram.com/reel/C8xyz_123/?igsh=abc"
    assert extrair_url_instagram(url1) == "https://www.instagram.com/reel/C8xyz_123/"

    # Formato Post clássico
    url2 = "https://instagram.com/p/DB123456789/"
    assert extrair_url_instagram(url2) == "https://www.instagram.com/reel/DB123456789/"

    # Link dentro de uma frase longa enviada no Telegram
    texto = "Olha esse repo sensacional aqui: https://www.instagram.com/reel/C9ABCdef123/ vale a pena ver!"
    assert extrair_url_instagram(texto) == "https://www.instagram.com/reel/C9ABCdef123/"

    # Texto sem link do Instagram
    assert extrair_url_instagram("https://youtube.com/shorts/123") is None
    assert extrair_url_instagram("Apenas um texto qualquer") is None


def test_formatar_stars():
    """Testa formatação de contagem de estrelas do GitHub."""
    assert formatar_stars(42) == "42"
    assert formatar_stars(850) == "850"
    assert formatar_stars(1200) == "1.2k"
    assert formatar_stars(8420) == "8.4k"
    assert formatar_stars(1500000) == "1.5M"


def test_formatar_data_relativa():
    """Testa formatação de proximidade temporal de commits."""
    assert formatar_data_relativa("") == "Desconhecido"
    # Formato ISO
    assert isinstance(formatar_data_relativa("2026-10-15T12:00:00Z"), str)


def test_schema_multimodal_collection():
    """Testa a validação do novo schema MultimodalReelAnalysis com múltiplos itens (1:N)."""
    from analyzer import MultimodalReelAnalysis, IdentifiedTechnologyItem

    analise = MultimodalReelAnalysis(
        is_collection=True,
        collection_title="Claude Web Design Toolkit",
        collection_overview="Conjunto de 5 ferramentas para design e automação web.",
        technologies=[
            IdentifiedTechnologyItem(
                tech_name="Taste",
                github_candidate="jaytel0/taste",
                summary="Biblioteca para design system minimalista.",
                install_commands="npx taste init"
            ),
            IdentifiedTechnologyItem(
                tech_name="Playwright CLI",
                github_candidate="microsoft/playwright",
                summary="CLI para testes e automação de browser.",
                install_commands="npm install -g @playwright/cli"
            )
        ]
    )

    assert analise.is_collection is True
    assert len(analise.technologies) == 2
    assert analise.technologies[0].tech_name == "Taste"
    assert analise.technologies[1].tech_name == "Playwright CLI"


def test_formatar_dossie_telegram_collection():
    """Testa a formatação rica de mensagem e inline keyboard para coleções no Telegram."""
    from researcher import ValidatedCollectionDossier, ValidatedTechnologyDossier
    from bot import formatar_dossie_telegram

    item1 = ValidatedTechnologyDossier(
        tech_name="Taste",
        summary="Design system minimalista para Claude.",
        audio_insights="Criador destaca facilidade de componentes.",
        video_insights="Mostra tela do terminal rodando npx taste.",
        install_command="npx taste init",
        repo_found=True,
        repo_name="jaytel0/taste",
        repo_url="https://github.com/jaytel0/taste",
        stars_display="2.1k",
        language="TypeScript"
    )

    item2 = ValidatedTechnologyDossier(
        tech_name="Playwright CLI",
        summary="Automação headless de navegação.",
        audio_insights="Destaca a rapidez de testes E2E.",
        video_insights="Exibe inspeção de snapshots web.",
        install_command="npm i -g @playwright/cli",
        repo_found=True,
        repo_name="microsoft/playwright",
        repo_url="https://github.com/microsoft/playwright",
        stars_display="70.5k",
        language="TypeScript"
    )

    col = ValidatedCollectionDossier(
        is_collection=True,
        collection_title="Claude Web Design Toolkit",
        collection_overview="Ecossistema completo para aceleração de UI.",
        items=[item1, item2]
    )

    texto, markup = formatar_dossie_telegram(col, "https://www.instagram.com/reel/DeXJcXmFLMv/")

    # Validações no texto da mensagem
    assert "Claude Web Design Toolkit" in texto
    assert "TOOLKIT / COMPILAÇÃO IDENTIFICADA" in texto
    assert "1️⃣ <b>Taste</b>" in texto
    assert "2️⃣ <b>Playwright CLI</b>" in texto
    assert "jaytel0/taste" in texto
    assert "microsoft/playwright" in texto

    # Validações no teclado inline
    assert markup is not None
    teclado = markup.get("inline_keyboard", [])
    # Botões individuais
    botoes_planos = [btn for row in teclado for btn in row]
    textos_botoes = [btn["text"] for btn in botoes_planos]

    assert any("Pesquisar Taste" in t for t in textos_botoes)
    assert any("Pesquisar Playwright" in t for t in textos_botoes)
    assert any("Pesquisar Toolkit Completo (2-em-1)" in t for t in textos_botoes)


def test_pesquisa_manager_cache_indexacao_individual(tmp_path, monkeypatch):
    """Testa se ao salvar uma coleção, as ferramentas individuais também são indexadas em cache."""
    import pesquisa_manager
    monkeypatch.setattr(pesquisa_manager, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(pesquisa_manager, "PEDIDOS_DIR", tmp_path / "pedidos")
    (tmp_path / "pedidos").mkdir(parents=True, exist_ok=True)

    from researcher import ValidatedCollectionDossier, ValidatedTechnologyDossier

    it = ValidatedTechnologyDossier(
        tech_name="Impeccable",
        summary="Ferramenta de tipografia e layout.",
        audio_insights="Comentário sobre fontes.",
        video_insights="Demonstração no browser.",
        install_command="npm install impeccable"
    )

    col = ValidatedCollectionDossier(
        is_collection=True,
        collection_title="Design Bundle",
        collection_overview="Pacote de design.",
        items=[it]
    )

    pesquisa_manager.salvar_dossie_cache("design-bundle", col, "https://instagram.com/reel/123")

    # Verifica se o dossiê da coleção existe
    col_cache = pesquisa_manager.obter_dossie_cache("design-bundle")
    assert col_cache is not None
    assert col_cache["is_collection"] is True
    assert col_cache["total_items"] == 1

    # Verifica se o dossiê individual do item foi indexado automaticamente
    item_cache = pesquisa_manager.obter_dossie_cache("impeccable")
    assert item_cache is not None
    assert item_cache["tech_name"] == "Impeccable"
    assert item_cache["parent_collection_slug"] == "design-bundle"

