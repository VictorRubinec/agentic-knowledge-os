"""Testes de exit code dos validadores de repositório em `scripts/`.

Cada teste monta um repositório mínimo em diretório temporário, com cópias
dos scripts em `scripts/` e das fixtures na raiz, e executa o validador via
subprocess, exatamente como o CI faz no repositório real.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

VALIDATOR_SCRIPTS = ("validar_links.py", "validar_frontmatter.py", "gerar_organization.py")

ORGANIZATION_TEMPLATE = """# ORGANIZATION.md

## Matriz de Categorias e Resumo de Documentos

<!-- AUTO-GENERATED:MATRIX:START -->
<!-- AUTO-GENERATED:MATRIX:END -->

---

## Índice de Palavras-Chave e Links Rápidos

<!-- AUTO-GENERATED:INDEX:START -->
<!-- AUTO-GENERATED:INDEX:END -->
"""


def make_repo(tmp_path: Path, *fixtures: str, organization: bool = False) -> Path:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for script in VALIDATOR_SCRIPTS:
        shutil.copy2(SCRIPTS_DIR / script, scripts / script)
    for fixture in fixtures:
        shutil.copy2(FIXTURES_DIR / fixture, tmp_path / fixture)
    if organization:
        (tmp_path / "ORGANIZATION.md").write_text(ORGANIZATION_TEMPLATE, encoding="utf-8")
    return tmp_path


def run_script(repo: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=repo,
    )


@pytest.mark.parametrize(
    ("fixture", "expected_code"),
    [
        ("valid.mdx", 0),
        ("broken_link.mdx", 1),
        ("missing_frontmatter.mdx", 0),
        ("missing_sections.mdx", 0),
    ],
)
def test_validar_links(tmp_path, fixture, expected_code):
    repo = make_repo(tmp_path, fixture)
    result = run_script(repo, "validar_links.py")
    assert result.returncode == expected_code, result.stdout
    if expected_code:
        assert "nao-existe.mdx" in result.stdout


def test_validar_links_ignores_code(tmp_path):
    repo = make_repo(tmp_path, "valid.mdx", "links_in_code.mdx")
    result = run_script(repo, "validar_links.py")
    assert result.returncode == 0, result.stdout


def test_validar_links_ignores_templates(tmp_path):
    repo = make_repo(tmp_path)
    shutil.copy2(FIXTURES_DIR / "broken_link.mdx", repo / "TEMPLATE_NOTA.mdx")
    result = run_script(repo, "validar_links.py")
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("fixture", "expected_code", "expected_message"),
    [
        ("valid.mdx", 0, None),
        ("broken_link.mdx", 0, None),
        ("missing_frontmatter.mdx", 1, "Frontmatter YAML ausente"),
        ("missing_sections.mdx", 1, "Linha do Tempo"),
    ],
)
def test_validar_frontmatter(tmp_path, fixture, expected_code, expected_message):
    repo = make_repo(tmp_path, fixture)
    result = run_script(repo, "validar_frontmatter.py")
    assert result.returncode == expected_code, result.stdout
    if expected_message:
        assert expected_message in result.stdout
    if fixture == "missing_sections.mdx":
        assert "Assuntos Relacionados" in result.stdout


def test_validators_ignore_tests_dir(tmp_path):
    repo = make_repo(tmp_path, "valid.mdx")
    shutil.copytree(FIXTURES_DIR, repo / "tests" / "fixtures")
    assert run_script(repo, "validar_links.py").returncode == 0
    assert run_script(repo, "validar_frontmatter.py").returncode == 0


def test_gerar_organization_check_in_sync(tmp_path):
    repo = make_repo(tmp_path, "valid.mdx", organization=True)
    assert run_script(repo, "gerar_organization.py", "--write").returncode == 0
    result = run_script(repo, "gerar_organization.py", "--check")
    assert result.returncode == 0, result.stdout
    assert "valid.mdx" in (repo / "ORGANIZATION.md").read_text(encoding="utf-8")


def test_gerar_organization_check_out_of_sync(tmp_path):
    repo = make_repo(tmp_path, "valid.mdx", organization=True)
    assert run_script(repo, "gerar_organization.py", "--write").returncode == 0
    shutil.copy2(FIXTURES_DIR / "missing_sections.mdx", repo / "missing_sections.mdx")
    result = run_script(repo, "gerar_organization.py", "--check")
    assert result.returncode == 1, result.stdout
    assert "desatualizado" in result.stdout


def test_gerar_organization_check_missing_file(tmp_path):
    repo = make_repo(tmp_path, "valid.mdx")
    assert run_script(repo, "gerar_organization.py", "--check").returncode == 1
