"""Testes automatizados da ferramenta oficial OptMem (optmem_memo.py)."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPTMEM_SCRIPT = REPO_ROOT / "scripts" / "optmem_memo.py"


def test_optmem_lifecycle(tmp_path: Path, monkeypatch):
    """Valida o ciclo de vida do OptMem: init -> note -> wake -> recall."""
    test_memory_dir = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_DIR", str(test_memory_dir))

    # 1. Init
    res_init = subprocess.run(
        [sys.executable, str(OPTMEM_SCRIPT), "init"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env={"MEMORY_DIR": str(test_memory_dir)}
    )
    assert res_init.returncode == 0, f"Falha no init: {res_init.stderr}"

    # 2. Note
    res_note = subprocess.run(
        [sys.executable, str(OPTMEM_SCRIPT), "note", "Teste de persistencia deterministica OptMem"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env={"MEMORY_DIR": str(test_memory_dir)}
    )
    assert res_note.returncode == 0, f"Falha no note: {res_note.stderr}"
    assert "Saved as #0." in res_note.stdout

    # 3. Recall
    res_recall = subprocess.run(
        [sys.executable, str(OPTMEM_SCRIPT), "recall", "deterministica"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env={"MEMORY_DIR": str(test_memory_dir)}
    )
    assert res_recall.returncode == 0
    assert "Teste de persistencia" in res_recall.stdout
