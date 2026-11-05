#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_wa_ingest.py
Suíte de testes automatizados para a esteira de Ingestão WhatsApp do Knowledge OS.
"""

import sys
import json
import pytest
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = WORKSPACE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wa_ingest_listener import processar_mensagem_whatsapp

def test_ingest_link_com_tags(tmp_path):
    temp_target = tmp_path / "test_captured_links.md"
    payload = {
        "event": "message.received",
        "sessionId": "session-12345",
        "timestamp": "2026-11-04T23:40:00",
        "data": {
            "from": "5511999999999@s.whatsapp.net",
            "pushName": "Dev Tester",
            "content": "Novo repositório: https://github.com/miqdadbadjuber/anti-slop #ia #qualidade"
        }
    }
    resultado = processar_mensagem_whatsapp(payload, target_file=temp_target)
    assert resultado["status"] == "success"
    assert resultado["type"] == "link_captured"
    assert resultado["url_count"] == 1
    assert resultado["sender"] == "Dev Tester"
    assert temp_target.exists()

def test_ingest_nota_de_texto(tmp_path):
    temp_target = tmp_path / "test_captured_links.md"
    payload = {
        "event": "message.received",
        "sessionId": "session-12345",
        "timestamp": "2026-11-04T23:41:00",
        "data": {
            "from": "5511999999999@s.whatsapp.net",
            "pushName": "Dev Tester",
            "content": "Lembrete: alinhar com a equipe da Join4 sobre a sprint de quinta-feira"
        }
    }
    resultado = processar_mensagem_whatsapp(payload, target_file=temp_target)
    assert resultado["status"] == "success"
    assert resultado["type"] == "note_logged"

def test_ingest_evento_ignorado():
    payload = {
        "event": "connection.update",
        "sessionId": "session-12345",
        "data": {"status": "open"}
    }
    resultado = processar_mensagem_whatsapp(payload)
    assert resultado["status"] == "ignored"

if __name__ == "__main__":
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        test_ingest_link_com_tags(Path(td))
        test_ingest_nota_de_texto(Path(td))
    test_ingest_evento_ignorado()
    print("Todos os testes de ingestão passaram com 100% de sucesso!")
