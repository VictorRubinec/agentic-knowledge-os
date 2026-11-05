"""Testes unitários e de integração para o Bot Remoto do Telegram do Knowledge OS."""

import json
from pathlib import Path
import pytest
import sys

# Garante importação a partir de scripts/ e do submódulo do analisador
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "projetos" / "analisador-instagram-telegram"))

from downloader import extrair_url_instagram, extrair_url_midia


def test_extrair_url_instagram_reels_e_posts():
    # Link direto de reel
    url1 = "https://www.instagram.com/reel/DfXFwwCDFMD/?vrfl=MXhqY2x6OGRkdGdmAA=="
    assert extrair_url_instagram(url1) == "https://www.instagram.com/reel/DfXFwwCDFMD/"

    # Link de post comum
    url2 = "https://instagram.com/p/C3XYZ123456/"
    assert extrair_url_instagram(url2) == "https://www.instagram.com/reel/C3XYZ123456/"

    # Link dentro de frase do usuário
    texto_usuario = "Dá uma olhada nesse reel incrível: https://www.instagram.com/reels/AB987654/ muito massa"
    assert extrair_url_instagram(texto_usuario) == "https://www.instagram.com/reel/AB987654/"

    # Não deve casar links aleatórios
    texto_outro = "Veja https://github.com/openai/whisper ou https://google.com"
    assert extrair_url_instagram(texto_outro) is None


def test_extrair_url_midia_youtube_shorts():
    yt_url = "https://www.youtube.com/shorts/dQw4w9WgXcQ?feature=share"
    assert extrair_url_midia(yt_url) == "https://www.youtube.com/shorts/dQw4w9WgXcQ"


def test_callback_parsing_estrutura():
    # Valida prefixes de callbacks usados no bot
    callbacks_teste = [
        ("pesq_init:meu-slug-123", "pesq_init", "meu-slug-123"),
        ("pesq_f:meu-slug-123:mercado_negocios", "pesq_f", "meu-slug-123"),
        ("pesq_p:meu-slug-123:dossie_executivo", "pesq_p", "meu-slug-123"),
        ("pesq_done:PED-20261105-01", "pesq_done", "PED-20261105-01"),
        ("approve_TASK-001_dossie.pdf", "approve", "TASK-001")
    ]

    for raw, prefix_esperado, valor_esperado in callbacks_teste:
        if raw.startswith("approve_"):
            partes = raw.split("_")
            assert partes[0] == prefix_esperado
            assert partes[1] == valor_esperado
        else:
            partes = raw.split(":")
            assert partes[0] == prefix_esperado
            assert partes[1] == valor_esperado


def test_autorizacao_usuario():
    allowed_id = "6085958682"

    def verificar_acesso(user_id):
        if not allowed_id or allowed_id.startswith("INSIRA_"):
            return True
        return str(user_id) == str(allowed_id)

    # Usuário homologado
    assert verificar_acesso("6085958682") is True
    assert verificar_acesso(6085958682) is True

    # Usuário não autorizado
    assert verificar_acesso("999999999") is False
    assert verificar_acesso("123456789") is False
