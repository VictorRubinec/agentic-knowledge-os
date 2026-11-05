#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/wa_ingest_listener.py
Receptor de Webhooks do WA-AKG Gateway para Ingestão Contínua no Knowledge OS.
Transforma links, mensagens de texto, tarefas e notas rápidas do WhatsApp
em registros estruturados na base de conhecimento sem intervenção manual.
"""

import sys
import os
import re
import json
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = WORKSPACE_DIR / "00-meta" / "historico_memoria"
CAPTURED_LINKS_FILE = WORKSPACE_DIR / "projetos" / "links-capturados.md"
EVENT_LOG_FILE = LOGS_DIR / "wa_ingest_events.jsonl"

WEBHOOK_SECRET = os.getenv("WA_INGEST_SECRET", "knowledge-os-secret")
DEFAULT_PORT = 5050

def garantir_diretorios():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not CAPTURED_LINKS_FILE.exists():
        CAPTURED_LINKS_FILE.write_text(
            "# Links Capturados via WhatsApp (Knowledge OS Ingestion)\n\n"
            "| # | Data / Hora | Origem | Remetente | Link / Conteúdo | Tags |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n",
            encoding="utf-8"
        )

def processar_mensagem_whatsapp(payload: dict, target_file: Path = None) -> dict:
    """Classifica e persiste a mensagem recebida."""
    garantir_diretorios()
    links_file = target_file or CAPTURED_LINKS_FILE
    
    event = payload.get("event")
    data = payload.get("data", {})
    session_id = payload.get("sessionId", "unknown")
    timestamp = payload.get("timestamp") or datetime.now().isoformat()
    
    # Salvar log bruto do evento
    with open(EVENT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        
    if event != "message.received":
        return {"status": "ignored", "reason": f"Event '{event}' not routed"}

    # Extrair corpo da mensagem
    conteudo = ""
    from_jid = data.get("from") or data.get("key", {}).get("remoteJid", "unknown")
    push_name = data.get("pushName") or "Desconhecido"
    
    if isinstance(data.get("content"), str):
        conteudo = data.get("content")
    elif isinstance(data.get("message"), dict):
        msg = data.get("message")
        conteudo = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text") or ""
    elif isinstance(data.get("text"), str):
        conteudo = data.get("text")

    conteudo = conteudo.strip()
    if not conteudo:
        return {"status": "empty_content"}

    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Detecção de URLs
    urls = re.findall(r'https?://[^\s]+', conteudo)
    if urls:
        total_linhas = len(links_file.read_text(encoding="utf-8").splitlines()) if links_file.exists() else 0
        
        novo_id = max(1, total_linhas - 3)
        tags = re.findall(r'#(\w+)', conteudo)
        tags_str = ", ".join(tags) if tags else "Sem tag"
        
        linha_tabela = f"| {novo_id} | {dt_str} | WhatsApp ({session_id[:8]}) | {push_name} | {conteudo} | {tags_str} |\n"
        with open(links_file, "a", encoding="utf-8") as f:
            f.write(linha_tabela)
            
        return {
            "status": "success",
            "type": "link_captured",
            "url_count": len(urls),
            "sender": push_name
        }

    # Anotação de texto comum
    return {
        "status": "success",
        "type": "note_logged",
        "sender": push_name,
        "length": len(conteudo)
    }

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = json.dumps({"status": "ok", "service": "Knowledge OS WA Ingest"}).encode("utf-8")
            self.wfile.write(resp)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/api/ingest" and self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Validação de Assinatura se configurada
        sig_header = self.headers.get("X-Webhook-Signature")
        if WEBHOOK_SECRET and sig_header:
            expected_sig = "sha256=" + hmac.new(WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig_header, expected_sig):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid signature"}).encode("utf-8"))
                return

        try:
            payload = json.loads(body.decode("utf-8"))
            result = processar_mensagem_whatsapp(payload)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        # Silenciar logs ruidosos de terminal
        pass

def iniciar_servidor(host: str = "127.0.0.1", port: int = DEFAULT_PORT):
    server = HTTPServer((host, port), WebhookHandler)
    print(f"[Knowledge OS] WA Ingest Listener ativo em http://{host}:{port}/api/ingest")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Knowledge OS] Servidor encerrado.")
        server.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Receptor de Webhooks do WA-AKG para o Knowledge OS")
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT, help="Porta de escuta HTTP")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de rede do host")
    parser.add_argument("--test-payload", "-t", action="store_true", help="Dispara um teste interno de ingestão")

    args = parser.parse_args()

    if args.test_payload:
        amostra = {
            "event": "message.received",
            "sessionId": "test-session-local",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "from": "5511999999999@s.whatsapp.net",
                "pushName": "Victor Teste",
                "content": "Confira este link do GitHub: https://github.com/academa-labs/manimgx #estudo #animacao"
            }
        }
        res = processar_mensagem_whatsapp(amostra)
        print("[TESTE INGESTÃO] Resultado:", json.dumps(res, indent=2))
    else:
        iniciar_servidor(args.host, args.port)
