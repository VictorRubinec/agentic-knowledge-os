"""Testes automatizados do motor unificado de geração de PDFs (gerar_pdf.py).

Valida a compilação de:
1. Artefatos HTML5 com diagramas Mermaid e Tailwind CSS.
2. Integridade dos arquivos gerados com pypdf.
3. Bloqueio preventivo de diagramas com erro de sintaxe.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest

pypdf = pytest.importorskip("pypdf", reason="Biblioteca 'pypdf' não instalada no ambiente.")
pytest.importorskip("playwright", reason="Biblioteca 'playwright' não instalada no ambiente.")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
GERAR_PDF_SCRIPT = SCRIPTS_DIR / "gerar_pdf.py"


def test_gerar_pdf_artefato_html(tmp_path: Path):
    """Testa a compilação direta de um artefato HTML para PDF A4."""
    html_sample = tmp_path / "teste_artefato.html"
    html_sample.write_text(
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Teste Automatizado</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white text-slate-800">
    <div class="document-container max-w-4xl mx-auto p-8">
        <header class="header-cover">
            <h1 class="text-2xl font-bold text-slate-900">Teste Automatizado de Artefato</h1>
        </header>
        <main>
            <p class="text-slate-600">Este é um documento de teste de integridade do pipeline Playwright.</p>
        </main>
    </div>
</body>
</html>
""",
        encoding="utf-8"
    )

    output_pdf = tmp_path / "teste_artefato.pdf"

    env = dict(sys.modules["os"].environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, str(GERAR_PDF_SCRIPT), str(html_sample), "-o", str(output_pdf)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=REPO_ROOT
    )

    stderr_text = result.stderr or ""
    if result.returncode != 0 and ("Executable doesn't exist" in stderr_text or "playwright install" in stderr_text):
        pytest.skip("Playwright Chromium browser não instalado neste ambiente.")

    assert result.returncode == 0, f"Falha na execução: {result.stderr}\n{result.stdout}"
    assert output_pdf.exists(), "O arquivo PDF de saída não foi gerado."

    # Validar integridade com pypdf
    reader = pypdf.PdfReader(str(output_pdf))
    assert len(reader.pages) >= 1, "O PDF gerado deve conter pelo menos 1 página."


def test_gerar_pdf_rejeita_mermaid_syntax_error(tmp_path: Path):
    """Garante que diagramas Mermaid com erro de sintaxe são bloqueados e abortam a compilação."""
    html_sample = tmp_path / "teste_mermaid_invalido.html"
    html_sample.write_text(
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Teste Erro Mermaid</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body class="bg-white text-slate-800">
    <div class="document-container max-w-4xl mx-auto p-8">
        <header class="header-cover">
            <h1 class="text-2xl font-bold text-slate-900">Teste Erro Mermaid</h1>
        </header>
        <main>
            <div class="mermaid">
flowchart TD
  subgraph Fase 1: Padronizacao CSS (SSOT)
    A --> B
  end
            </div>
        </main>
    </div>
    <script>mermaid.initialize({startOnLoad: true});</script>
</body>
</html>
""",
        encoding="utf-8"
    )

    output_pdf = tmp_path / "teste_mermaid_invalido.pdf"

    env = dict(sys.modules["os"].environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, str(GERAR_PDF_SCRIPT), str(html_sample), "-o", str(output_pdf)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=REPO_ROOT
    )

    assert result.returncode != 0, "O motor de PDF deveria falhar ao encontrar erro de sintaxe no Mermaid."
    assert not output_pdf.exists(), "O PDF não deve ser gerado quando houver erro no diagrama Mermaid."
