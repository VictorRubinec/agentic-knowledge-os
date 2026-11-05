#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor de Automação do Repositório (Second Brain) para Shard Cloud
Executa validações contínuas, testes e compilação de PDFs via API/Webhooks.
"""

import subprocess
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(
    title="Second Brain Automation API",
    description="Motor de automação, validação e compilação de PDFs do Repositório de Anotações",
    version="1.0.0"
)

WORKSPACE_DIR = Path(__file__).resolve().parent.parent

class ValidateRequest(BaseModel):
    check_links: bool = True
    check_frontmatter: bool = True
    check_organization: bool = True

class PDFRequest(BaseModel):
    filepath: str
    theme: str = "corporate"
    check_only: bool = False

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Second Brain Automation Server",
        "platform": "Shard Cloud",
        "workspace": str(WORKSPACE_DIR)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/validate")
def run_validations(req: ValidateRequest):
    results = {}
    
    if req.check_frontmatter:
        res = subprocess.run([sys.executable, "scripts/validar_frontmatter.py"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
        results["frontmatter"] = {"exit_code": res.returncode, "output": res.stdout}
        
    if req.check_links:
        res = subprocess.run([sys.executable, "scripts/validar_links.py"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
        results["links"] = {"exit_code": res.returncode, "output": res.stdout}
        
    if req.check_organization:
        res = subprocess.run([sys.executable, "scripts/gerar_organization.py", "--check"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
        results["organization"] = {"exit_code": res.returncode, "output": res.stdout}

    return {"status": "success", "results": results}

@app.post("/api/generate-pdf")
def generate_pdf(req: PDFRequest):
    # Proteção estrita contra Path Traversal (SAST Hardening)
    try:
        target = (WORKSPACE_DIR / req.filepath).resolve()
        workspace_resolved = WORKSPACE_DIR.resolve()
        if not str(target).startswith(str(workspace_resolved)):
            raise HTTPException(status_code=403, detail="Acesso negado: caminho fora dos limites do workspace.")
    except Exception:
        raise HTTPException(status_code=400, detail="Caminho de arquivo inválido.")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {req.filepath}")

    # Whitelist de temas permitidos
    allowed_themes = {"corporate", "join4", "somos1", "rpg", "minimal"}
    if req.theme not in allowed_themes:
        raise HTTPException(status_code=400, detail=f"Tema não reconhecido: {req.theme}. Permitidos: {allowed_themes}")

    cmd = [sys.executable, "scripts/gerar_pdf.py", str(target), "--theme", req.theme]
    if req.check_only:
        cmd.append("--check-only")

    res = subprocess.run(cmd, cwd=WORKSPACE_DIR, capture_output=True, text=True)
    return {
        "status": "success" if res.returncode == 0 else "error",
        "exit_code": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
