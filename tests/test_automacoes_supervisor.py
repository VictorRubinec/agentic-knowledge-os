"""Testes unitários e de integridade para o Supervisor de Automações do Knowledge OS."""

import json
from pathlib import Path
import pytest
import sys

# Garante importação a partir de scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from iniciar_automacoes import (
    SERVICOS,
    ROOT_DIR,
    SCRIPTS_DIR,
    META_DIR,
    PID_FILE,
)


def test_servicos_registry_existencia_arquivos():
    """Valida se todos os scripts registrados em SERVICOS realmente existem no disco."""
    for nome, cfg in SERVICOS.items():
        if "script" in cfg:
            script_path = cfg["script"]
            assert script_path.exists(), f"Script do serviço '{nome}' não existe: {script_path}"
        assert cfg.get("descricao"), f"Serviço '{nome}' sem descrição."
        assert cfg.get("grupo") in ["core", "hermes", "workers", "scrapers"], f"Grupo inválido para '{nome}'"


def test_portas_unicas_servicos_sem_colisao():
    """Garante que não existem duas portas em conflito no supervisor."""
    portas = {}
    for nome, cfg in SERVICOS.items():
        porta = cfg.get("porta")
        if porta:
            assert porta not in portas, f"Conflito de porta {porta} entre '{nome}' e '{portas[porta]}'"
            portas[porta] = nome


def test_pid_file_lifecycle(tmp_path, monkeypatch):
    """Testa leitura e escrita segura do arquivo de PIDs."""
    test_pid_path = tmp_path / ".pids_test.json"
    monkeypatch.setattr("iniciar_automacoes.PID_FILE", test_pid_path)

    pids_dummy = {
        "telegram-bot": 1234,
        "wa-ingest": 5678
    }

    test_pid_path.write_text(json.dumps(pids_dummy), encoding="utf-8")
    assert test_pid_path.exists()

    lido = json.loads(test_pid_path.read_text(encoding="utf-8"))
    assert lido["telegram-bot"] == 1234
    assert lido["wa-ingest"] == 5678
