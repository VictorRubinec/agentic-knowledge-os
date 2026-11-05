#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/clickup_webhook_listener.py
Servidor Listener de Webhooks do ClickUp e Gerenciador de Webhooks da Join4.
"""

import sys
import os
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import threading

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from analisador_clickup import api_request, sincronizar_tarefa, TARGET_USER_ID, get_token

TEAM_ID = "90132893525"  # Join4 Produtos

class ClickUpWebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/", "/health"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "online",
                "service": "ClickUp IA Webhook Listener",
                "team_id": TEAM_ID,
                "target_user_id": TARGET_USER_ID
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path in ["/webhook", "/clickup/webhook"]:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode("utf-8"))
                event = payload.get("event", "desconhecido")
                task_id = payload.get("task_id")
                webhook_id = payload.get("webhook_id")
                
                print(f"\n[WEBHOOK RECEBIDO] Evento: {event} | Task ID: {task_id} (Webhook: {webhook_id})")

                # Responde 200 OK imediatamente para o ClickUp não retentar
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "received", "task_id": task_id}).encode("utf-8"))

                # Dispara a análise em background para não travar a resposta HTTP
                if task_id:
                    def executar_analise():
                        try:
                            print(f"[IA WORKER] Iniciando análise para tarefa {task_id}...")
                            resultado = sincronizar_tarefa(task_id, post_comment=True)
                            if resultado:
                                print(f"[IA WORKER] Análise concluída e registrada em {resultado.name}!")
                        except Exception as e:
                            print(f"[IA WORKER ERRO] Falha ao processar tarefa {task_id}: {e}")

                    t = threading.Thread(target=executar_analise, daemon=True)
                    t.start()
            except Exception as e:
                print(f"[ERRO PAYLOAD] Falha ao decodificar payload: {e}")
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silencia logs padrão excessivos do http.server
        sys.stderr.write(f"[HTTP] {self.address_string()} - {args[0]} {args[1]}\n")

def registrar_webhook(endpoint_url):
    print(f"[INFO] Registrando webhook no ClickUp para endpoint: {endpoint_url}")
    body = {
        "endpoint": endpoint_url,
        "events": [
            "taskCreated",
            "taskUpdated",
            "taskAssigneeUpdated",
            "taskCommentPosted"
        ]
    }
    resp = api_request(f"/team/{TEAM_ID}/webhook", method="POST", body=body)
    webhook = resp.get("webhook", {})
    w_id = webhook.get("id")
    print(f"[OK] Webhook registrado com sucesso!")
    print(f"     ID: {w_id}")
    print(f"     Endpoint: {webhook.get('endpoint')}")
    print(f"     Eventos: {', '.join(webhook.get('events', []))}")
    return resp

def listar_webhooks():
    print(f"[INFO] Listando webhooks ativos no workspace {TEAM_ID}...")
    resp = api_request(f"/team/{TEAM_ID}/webhook", method="GET")
    webhooks = resp.get("webhooks", [])
    print(f"Total de webhooks: {len(webhooks)}\n")
    for idx, w in enumerate(webhooks, 1):
        print(f"[{idx}] ID: {w.get('id')}")
        print(f"    Endpoint: {w.get('endpoint')}")
        print(f"    Eventos: {', '.join(w.get('events', []))}")
        print(f"    Criado por: {w.get('userid')} | Saúde: {w.get('health', {}).get('status')}")
        print("-" * 60)
    return webhooks

def deletar_webhook(webhook_id):
    print(f"[INFO] Deletando webhook {webhook_id}...")
    resp = api_request(f"/webhook/{webhook_id}", method="DELETE")
    print(f"[OK] Webhook {webhook_id} removido com sucesso!")
    return resp

def iniciar_servidor(porta=8088):
    server_address = ("0.0.0.0", porta)
    httpd = HTTPServer(server_address, ClickUpWebhookHandler)
    print("=" * 70)
    print(f" ClickUp IA Webhook Listener — Porta {porta}")
    print("=" * 70)
    print(f" Healthcheck: http://localhost:{porta}/health")
    print(f" Webhook URL: http://localhost:{porta}/webhook")
    print(" Aguardando eventos do ClickUp... Pressione Ctrl+C para encerrar.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Encerrando servidor.")
        httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="ClickUp Webhook Listener & Manager")
    parser.add_argument("--start", action="store_true", help="Iniciar o servidor listener de webhooks")
    parser.add_argument("--port", type=int, default=8088, help="Porta do servidor (padrão: 8088)")
    parser.add_argument("--register", metavar="URL", help="Registrar uma nova URL de webhook no ClickUp")
    parser.add_argument("--list", action="store_true", help="Listar webhooks existentes no ClickUp")
    parser.add_argument("--delete", metavar="WEBHOOK_ID", help="Deletar um webhook pelo ID")

    args = parser.parse_args()

    if args.register:
        registrar_webhook(args.register)
    elif args.list:
        listar_webhooks()
    elif args.delete:
        deletar_webhook(args.delete)
    elif args.start:
        iniciar_servidor(args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
