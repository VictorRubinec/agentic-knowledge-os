"""Testes unitários e de integração para o motor Hermes (Harness Autônomo e Cronograma)."""

import datetime
import json
from pathlib import Path
import pytest
import sys

# Garante importação a partir de scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from hermes_agent import (
    sanitizar_mermaid,
    carregar_cronograma,
    salvar_cronograma,
    obter_tarefa_elegivel,
)


def test_sanitizar_mermaid_corrige_aspas_puras():
    html_raw = """
    <pre class="mermaid">
flowchart TD
    "CLIENT_A" --> "SERVER_B"
    "SERVER_B" --> "DB_C"
    </pre>
    """
    html_limpo = sanitizar_mermaid(html_raw)
    assert '    "CLIENT_A" -->' not in html_limpo
    assert 'CLIENT_A["CLIENT_A"]' in html_limpo
    assert 'SERVER_B["SERVER_B"]' in html_limpo
    assert 'DB_C["DB_C"]' in html_limpo


def test_sanitizar_mermaid_corrige_arestas_com_aspas():
    html_raw = """
    <pre class="mermaid">
flowchart TD
    A -- "TEXTO RÓTULO" --> B
    B -- STATUS --> C
    C -->| FOO["BAR"]| D
    </pre>
    """
    html_limpo = sanitizar_mermaid(html_raw)
    assert '-->|"TEXTO RÓTULO"|' in html_limpo
    assert '-->|"STATUS"|' in html_limpo
    assert '-->|"BAR"|' in html_limpo


def test_sanitizar_mermaid_preserva_diagramas_validos():
    html_valido = """
    <pre class="mermaid">
flowchart TD
    A["Cliente API"] -->|"Requisição JSON"| B["Servidor FastMCP"]
    B --> C[("PostgreSQL")]
    </pre>
    """
    html_processado = sanitizar_mermaid(html_valido)
    assert 'A["Cliente API"]' in html_processado
    assert '-->|"Requisição JSON"|' in html_processado
    assert 'C[("PostgreSQL")]' in html_processado


def test_cronograma_loading(tmp_path, monkeypatch):
    test_cron_file = tmp_path / "cronograma_test.json"
    dummy_data = {
        "pausado": False,
        "cota_maxima_diaria": 2,
        "slots_horario": ["08:30", "19:30"],
        "silenciador_noturno": {"ativo": True, "inicio": "23:00", "fim": "07:00"}
    }
    test_cron_file.write_text(json.dumps(dummy_data), encoding="utf-8")

    monkeypatch.setattr("hermes_agent.CRONOGRAMA_FILE", test_cron_file)
    carregado = carregar_cronograma()
    assert carregado["pausado"] is False
    assert carregado["cota_maxima_diaria"] == 2

    salvar_cronograma({"pausado": True})
    assert json.loads(test_cron_file.read_text(encoding="utf-8"))["pausado"] is True


def test_obter_tarefa_elegivel_bloqueio_pausado():
    cronograma = {"pausado": True}
    tasks = [{"id": "TASK-1", "status": "pending", "scheduled_for": "2026-11-05T08:30:00"}]
    tarefa, motivo = obter_tarefa_elegivel(tasks, cronograma)
    assert tarefa is None
    assert motivo == "cronograma_pausado"


def test_obter_tarefa_elegivel_bloqueio_silencio_noturno(monkeypatch):
    cronograma = {
        "pausado": False,
        "silenciador_noturno": {"ativo": True, "inicio": "23:00", "fim": "07:00"}
    }
    tasks = [{"id": "TASK-1", "status": "pending", "scheduled_for": "2026-11-05T03:00:00"}]

    # Simula horário 03:30 da madrugada
    class FakeDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 5, 3, 30, 0)

    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    tarefa, motivo = obter_tarefa_elegivel(tasks, cronograma)
    assert tarefa is None
    assert "silenciador_noturno" in motivo


def test_obter_tarefa_elegivel_bloqueio_descanso_domingo(monkeypatch):
    cronograma = {
        "pausado": False,
        "silenciador_noturno": {"ativo": False}
    }
    tasks = [{"id": "TASK-1", "status": "pending", "scheduled_for": "2026-11-08T08:30:00"}]

    # Simula um Domingo (weekday = 6)
    class FakeDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 8, 12, 0, 0)

    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    tarefa, motivo = obter_tarefa_elegivel(tasks, cronograma)
    assert tarefa is None
    assert "domingo" in motivo or "descanso" in motivo


def test_obter_tarefa_elegivel_bloqueio_cota_atingida(monkeypatch):
    cronograma = {
        "pausado": False,
        "cota_maxima_diaria": 2,
        "silenciador_noturno": {"ativo": False}
    }

    # Simula 2 tarefas já completadas hoje
    hoje_str = "2026-11-05"
    tasks = [
        {"id": "TASK-1", "status": "completed", "completed_at": f"{hoje_str}T09:00:00"},
        {"id": "TASK-2", "status": "completed", "completed_at": f"{hoje_str}T11:00:00"},
        {"id": "TASK-3", "status": "pending", "scheduled_for": f"{hoje_str}T14:00:00"}
    ]

    class FakeDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 5, 14, 0, 0)

    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    tarefa, motivo = obter_tarefa_elegivel(tasks, cronograma)
    assert tarefa is None
    assert "cota_diaria_atingida" in motivo


def test_obter_tarefa_elegivel_sucesso_horario_chegou(monkeypatch):
    cronograma = {
        "pausado": False,
        "cota_maxima_diaria": 5,
        "silenciador_noturno": {"ativo": False}
    }

    # Tarefa agendada para as 08:30, agora são 08:35
    hoje_str = "2026-11-05"
    tasks = [
        {"id": "TASK-OK", "status": "pending", "scheduled_for": f"{hoje_str}T08:30:00"}
    ]

    class FakeDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 5, 8, 35, 0)

    monkeypatch.setattr(datetime, "datetime", FakeDateTime)

    tarefa, motivo = obter_tarefa_elegivel(tasks, cronograma)
    assert tarefa is not None
    assert tarefa["id"] == "TASK-OK"
    assert "ok_slot_atingido" in motivo
