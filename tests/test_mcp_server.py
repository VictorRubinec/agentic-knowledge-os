"""Testes automatizados do servidor MCP nativo (scripts/knowledge_os_mcp.py)."""

import sys
from pathlib import Path
import pytest

pytest.importorskip("mcp", reason="Biblioteca 'mcp' não instalada no ambiente.")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.knowledge_os_mcp import server, search_knowledge


def test_mcp_tools_registered():
    """Valida se as ferramentas essenciais estão expostas no servidor MCP."""
    tools = [t.name for t in server._tool_manager.list_tools()]
    assert "generate_pdf" in tools
    assert "validate_document" in tools
    assert "search_knowledge" in tools
    assert "optmem_record" in tools
    assert "optmem_wake" in tools
    assert "optmem_recall" in tools
    assert "pesquisar_video_multimodal" in tools
    assert "wa_ingest_status" in tools


def test_mcp_search_knowledge():
    """Valida a funcionalidade de busca textual nas notas."""
    res = search_knowledge(query="Knowledge", category="exemplos")
    assert "exemplo_artefato_executivo.html" in res or "resultado(s)" in res
