#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/iniciar_automacoes.py
=============================================================================
ORQUESTRADOR E SUPERVISOR DE AUTOMAÇÕES DO KNOWLEDGE OS
Central de inicialização, monitoramento e gerenciamento de ciclo de vida
para todos os serviços, listeners e agentes em background do ecossistema.

Serviços Gerenciados:
  - telegram-bot       : scripts/telegram_remote_bot.py (Centro de comando Telegram)
  - wa-ingest          : scripts/wa_ingest_listener.py (Listener de webhook WhatsApp :5050)
  - clickup-listener   : scripts/clickup_webhook_listener.py (Listener ClickUp Join4 :5000)
  - api-server         : scripts/server.py (API FastAPI de automações e PDFs :8000)
  - hermes-worker      : scripts/hermes_agent.py --worker (Harness autônomo noturno)

Comandos Principais:
  python scripts/iniciar_automacoes.py status
  python scripts/iniciar_automacoes.py start [--all | --core | --hermes | --service NOME]
  python scripts/iniciar_automacoes.py stop
  python scripts/iniciar_automacoes.py restart
  python scripts/iniciar_automacoes.py run [--all | --core | --hermes]
  python scripts/iniciar_automacoes.py logs [NOME_SERVICO] [--lines 50]
  python scripts/iniciar_automacoes.py autostart [--install | --remove | --status] [--preset all|core]
=============================================================================
"""

import sys
import os
import json
import time
import signal
import socket
import argparse
import datetime
import subprocess
import threading
from pathlib import Path

# Suporte UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
META_DIR = ROOT_DIR / "00-meta"
LOGS_DIR = META_DIR / "logs"
PID_FILE = META_DIR / ".pids_automacoes.json"

TASK_SCHEDULER_NAME = "KnowledgeOS_Automacoes"

def get_python_exec(headless: bool = False) -> str:
    py_exec = Path(sys.executable)
    if headless and sys.platform == "win32":
        pyw = py_exec.parent / "pythonw.exe"
        if pyw.exists():
            return str(pyw)
    return sys.executable

SERVICOS = {
    "telegram-bot": {
        "descricao": "Bot Remoto do Telegram (Comandos, Linters & Aprovações)",
        "script": SCRIPTS_DIR / "telegram_remote_bot.py",
        "script_identifier": "telegram_remote_bot.py",
        "args": [],
        "porta": None,
        "grupo": "core"
    },
    "wa-ingest": {
        "descricao": "Webhook WhatsApp (Ingestão Automática de Notas e Links)",
        "script": SCRIPTS_DIR / "wa_ingest_listener.py",
        "script_identifier": "wa_ingest_listener.py",
        "args": [],
        "porta": 5050,
        "grupo": "core"
    },
    "clickup-listener": {
        "descricao": "Webhook Listener ClickUp (Sincronização Join4)",
        "script": SCRIPTS_DIR / "clickup_webhook_listener.py",
        "script_identifier": "clickup_webhook_listener.py",
        "args": [],
        "porta": 5000,
        "grupo": "core"
    },
    "api-server": {
        "descricao": "FastAPI Server (Compilação de PDFs, Testes & MCP Backend)",
        "module": "uvicorn",
        "script_identifier": "scripts.server:app",
        "args": ["scripts.server:app", "--host", "0.0.0.0", "--port", "8000"],
        "porta": 8000,
        "grupo": "core"
    },
    "hermes-worker": {
        "descricao": "Hermes Autonomous Harness (Loop Noturno e Fila de Metas)",
        "script": SCRIPTS_DIR / "hermes_agent.py",
        "script_identifier": "hermes_agent.py",
        "args": ["--worker", "--interval", "20"],
        "porta": None,
        "grupo": "hermes"
    },
    "curador-temas": {
        "descricao": "Curador e Scraper de Temas Técnicos (HN & GitHub Trending)",
        "script": SCRIPTS_DIR / "curador_temas_scraper.py",
        "script_identifier": "curador_temas_scraper.py",
        "args": ["--daemon", "--interval", "3600"],
        "porta": None,
        "grupo": "hermes"
    }
}


def carregar_pids():
    if not PID_FILE.exists():
        return {}
    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_pids(pids):
    META_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")


def porta_esta_aberta(porta: int) -> bool:
    if not porta:
        return False
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=0.2):
            return True
    except Exception:
        return False


def checar_pid_nativo(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_process = kernel32.OpenProcess(0x1000, False, pid)
            if not h_process:
                return False
            exit_code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(h_process, ctypes.byref(exit_code))
            kernel32.CloseHandle(h_process)
            return exit_code.value == 259  # STILL_ACTIVE
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False


def obter_processos_python_sistema():
    """Retorna lista de (pid, command_line) dos processos Python ativos no Windows."""
    processos = []
    if sys.platform != "win32":
        return processos
    try:
        cmd = ["powershell", "-NoProfile", "-Command", 
               "Get-CimInstance Win32_Process -Filter \"Name LIKE 'python%'\" | Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            raw = res.stdout.strip()
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                pid = item.get("ProcessId")
                cline = item.get("CommandLine") or ""
                if pid:
                    processos.append((int(pid), cline))
    except Exception:
        pass
    return processos


def identificar_servico_vivo(nome_servico: str, info: dict, pids_salvos: dict, processos_sistema: list = None):
    # 1. Se tem porta aberta e responde
    if info.get("porta") and porta_esta_aberta(info["porta"]):
        # Tentar achar o PID real pelo sistema se o salvo não estiver ativo
        pid_salvo = pids_salvos.get(nome_servico)
        if pid_salvo and checar_pid_nativo(pid_salvo):
            return True, pid_salvo
        if processos_sistema:
            for pid, cline in processos_sistema:
                if info["script_identifier"] in cline:
                    return True, pid
        return True, (pid_salvo or "-")

    # 2. Checar PID salvo diretamente
    pid_salvo = pids_salvos.get(nome_servico)
    if pid_salvo and checar_pid_nativo(pid_salvo):
        return True, pid_salvo

    # 3. Varredura por script_identifier na linha de comando
    if processos_sistema:
        for pid, cline in processos_sistema:
            if info["script_identifier"] in cline:
                return True, pid

    return False, None


def selecionar_servicos(args):
    selecionados = {}
    if getattr(args, "service", None):
        nome = args.service.strip().lower()
        if nome in SERVICOS:
            selecionados[nome] = SERVICOS[nome]
        else:
            print(f"[Erro] Serviço desconhecido: '{nome}'. Opções: {list(SERVICOS.keys())}")
            sys.exit(1)
    elif getattr(args, "hermes", False):
        selecionados = {k: v for k, v in SERVICOS.items() if v["grupo"] == "hermes"}
    elif getattr(args, "core", False):
        selecionados = {k: v for k, v in SERVICOS.items() if v["grupo"] == "core"}
    else:
        selecionados = SERVICOS
    return selecionados


def construir_comando(info, headless: bool = False):
    py_bin = get_python_exec(headless=headless)
    if "module" in info:
        return [py_bin, "-m", info["module"]] + info["args"]
    else:
        return [py_bin, str(info["script"])] + info["args"]


def cmd_status():
    pids = carregar_pids()
    processos_sistema = obter_processos_python_sistema()

    print("\n" + "=" * 92)
    print(f"{'SERVIÇO':<20} | {'STATUS':<12} | {'PID':<8} | {'PORTA':<8} | {'DESCRIÇÃO'}")
    print("-" * 92)

    novos_pids = dict(pids)
    for nome, info in SERVICOS.items():
        vivo, pid_real = identificar_servico_vivo(nome, info, pids, processos_sistema)
        status_str = "🟢 ATIVO" if vivo else "⚪ INATIVO"
        pid_str = str(pid_real) if pid_real else "-"
        porta_str = str(info["porta"]) if info["porta"] else "-"
        print(f"{nome:<20} | {status_str:<12} | {pid_str:<8} | {porta_str:<8} | {info['descricao']}")
        if vivo and pid_real and isinstance(pid_real, int):
            novos_pids[nome] = pid_real

    salvar_pids(novos_pids)
    print("=" * 92)
    
    # Status de Autostart
    autostart_ativo = verificar_autostart_ativo()
    autostart_str = "🟢 HABILITADO (Inicia com o Windows)" if autostart_ativo else "⚪ DESABILITADO"
    print(f" Inicialização Automática com o PC: {autostart_str}\n")


def cmd_run(args):
    """Executa em foreground com multiplexação de saída e shutdown limpo via Ctrl+C."""
    alvos = selecionar_servicos(args)
    print("\n" + "=" * 80)
    print(f"🚀 INICIALIZANDO SUPERVISOR DE AUTOMAÇÕES (Knowledge OS)")
    print(f"   Serviços selecionados: {', '.join(alvos.keys())}")
    print(f"   Pressione Ctrl+C a qualquer momento para desligamento gracioso.")
    print("=" * 80 + "\n")

    processos = {}
    threads = []
    stop_event = threading.Event()

    def stream_output(service_name, pipe):
        prefix = f"[{service_name.upper():<16}]"
        try:
            for line in iter(pipe.readline, ''):
                if stop_event.is_set():
                    break
                line_str = line.strip()
                if line_str:
                    print(f"{prefix} {line_str}", flush=True)
        except Exception:
            pass

    try:
        for nome, info in alvos.items():
            print(f"🟢 [Supervisor] Iniciando '{nome}' ({info['descricao']})...")
            cmd = construir_comando(info, headless=False)
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=ROOT_DIR
            )
            processos[nome] = p
            t = threading.Thread(target=stream_output, args=(nome, p.stdout), daemon=True)
            t.start()
            threads.append(t)
            time.sleep(0.3)

        print("\n✨ Todos os serviços iniciados. Monitorando atividade...\n")

        while True:
            time.sleep(1)
            for nome, p in list(processos.items()):
                ret = p.poll()
                if ret is not None and not stop_event.is_set():
                    print(f"⚠️  [Supervisor] O serviço '{nome}' encerrou com código {ret}.")

    except KeyboardInterrupt:
        print("\n\n🛑 [Supervisor] Interrupção detectada (Ctrl+C). Encerrando serviços...")
        stop_event.set()
        for nome, p in processos.items():
            print(f"   Encerrando '{nome}' (PID {p.pid})...")
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("✅ [Supervisor] Todos os serviços foram desligados com sucesso.\n")


def cmd_start(args):
    """Inicia serviços em background headless 100% silencioso e grava logs em arquivos."""
    alvos = selecionar_servicos(args)
    pids = carregar_pids()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    processos_sistema = obter_processos_python_sistema()

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    print("\n🟢 Inicializando serviços em background (Headless):")
    for nome, info in alvos.items():
        vivo, pid_atual = identificar_servico_vivo(nome, info, pids, processos_sistema)
        if vivo:
            print(f"   • {nome}: já está em execução (PID {pid_atual})")
            continue

        log_file_path = LOGS_DIR / f"{nome}.log"
        log_file = open(log_file_path, "a", encoding="utf-8", buffering=1)

        creationflags = 0
        if sys.platform == "win32":
            creationflags = 0x08000000 | subprocess.CREATE_NEW_PROCESS_GROUP  # CREATE_NO_WINDOW

        cmd = construir_comando(info, headless=True)
        p = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=ROOT_DIR,
            env=env,
            creationflags=creationflags
        )
        pids[nome] = p.pid
        print(f"   • {nome}: iniciado com sucesso (PID {p.pid}) -> Log: 00-meta/logs/{nome}.log")
        time.sleep(0.4)

    salvar_pids(pids)
    print("\nUse 'python scripts/iniciar_automacoes.py status' para monitorar.")
    print("Use 'python scripts/iniciar_automacoes.py logs [servico]' para visualizar os logs.\n")


def cmd_stop():
    pids = carregar_pids()
    processos_sistema = obter_processos_python_sistema()

    print("\n🛑 Encerrando serviços em execução:")
    novos_pids = {}

    for nome, info in SERVICOS.items():
        vivo, pid = identificar_servico_vivo(nome, info, pids, processos_sistema)
        if vivo and pid and isinstance(pid, int):
            print(f"   • Encerrando {nome} (PID {pid})...")
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
            except Exception as e:
                print(f"     Aviso ao encerrar PID {pid}: {e}")
        else:
            print(f"   • {nome} já estava inativo.")

    salvar_pids(novos_pids)
    print("✅ Todos os serviços parados.\n")


def cmd_logs(service: str = None, lines: int = 50):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if service:
        service = service.strip().lower()
        log_file = LOGS_DIR / f"{service}.log"
        if not log_file.exists():
            print(f"[Logs] Nenhum log encontrado para o serviço '{service}'.")
            return
        print(f"\n--- Últimas {lines} linhas de {service}.log ---")
        conteudo = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        for linha in conteudo[-lines:]:
            print(linha)
        print("------------------------------------------\n")
    else:
        print("\nArquivos de Log Disponíveis em 00-meta/logs/:")
        for lf in LOGS_DIR.glob("*.log"):
            tamanho_kb = lf.stat().st_size / 1024
            print(f"   • {lf.stem:<18}: {tamanho_kb:6.1f} KB ({lf.name})")
        print("\nPara visualizar: python scripts/iniciar_automacoes.py logs <servico>\n")


def get_startup_dir() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return None


def get_vbs_startup_path() -> Path:
    startup_dir = get_startup_dir()
    if startup_dir:
        return startup_dir / "KnowledgeOS_Automacoes.vbs"
    return None


def verificar_autostart_ativo() -> bool:
    vbs_path = get_vbs_startup_path()
    if vbs_path and vbs_path.exists():
        return True
    # Checar também Agendador de Tarefas
    try:
        res = subprocess.run(["schtasks", "/query", "/tn", TASK_SCHEDULER_NAME], capture_output=True, text=True)
        if res.returncode == 0:
            return True
    except Exception:
        pass
    return False


def cmd_autostart(install: bool, remove: bool, preset: str = "all"):
    vbs_path = get_vbs_startup_path()
    pyw_bin = get_python_exec(headless=True)
    script_path = ROOT_DIR / "scripts" / "iniciar_automacoes.py"
    flag = f"--{preset}"

    if remove:
        # 1. Remover do Startup Folder
        if vbs_path and vbs_path.exists():
            vbs_path.unlink()
            print(f"   • Removido do Startup: {vbs_path.name}")
        # 2. Remover do Agendador de Tarefas
        try:
            subprocess.run(["schtasks", "/delete", "/tn", TASK_SCHEDULER_NAME, "/f"], capture_output=True)
            print(f"   • Removido do Agendador de Tarefas ({TASK_SCHEDULER_NAME})")
        except Exception:
            pass
        print("✅ Inicialização automática com o PC desativada com sucesso.\n")
        return

    if install:
        # Criar Script VBS 100% silencioso no Startup Folder usando Chr(34) para aspas seguras
        vbs_content = f'''Dim WshShell, cmd
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{ROOT_DIR}"
cmd = Chr(34) & "{pyw_bin}" & Chr(34) & " " & Chr(34) & "{script_path}" & Chr(34) & " start {flag}"
WshShell.Run cmd, 0, False
Set WshShell = Nothing
'''
        vbs_encoding = "utf-16" if sys.platform == "win32" else "utf-8"
        if vbs_path:
            vbs_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                vbs_path.write_text(vbs_content, encoding=vbs_encoding)
            except Exception:
                vbs_path.write_text(vbs_content, encoding="utf-8")

        # Cópia no repositório para backup
        repo_vbs = SCRIPTS_DIR / "iniciar_automacoes_headless.vbs"
        try:
            repo_vbs.write_text(vbs_content, encoding=vbs_encoding)
        except Exception:
            repo_vbs.write_text(vbs_content, encoding="utf-8")

        # 2. Registrar no Windows Task Scheduler (No logon, headless)
        try:
            tr_cmd = f'"{pyw_bin}" "{script_path}" start {flag}'
            sch_cmd = [
                "schtasks", "/create",
                "/tn", TASK_SCHEDULER_NAME,
                "/tr", tr_cmd,
                "/sc", "onlogon",
                "/rl", "limited",
                "/f"
            ]
            subprocess.run(sch_cmd, capture_output=True, text=True)
        except Exception as e:
            print(f"   Aviso Task Scheduler: {e}")

        print("=" * 80)
        print("🎉 INICIALIZAÇÃO AUTOMÁTICA CONFIGURADA COM SUCESSO!")
        print("=" * 80)
        print(f"• Método 1: Pasta Inicializar do Windows ({vbs_path})")
        print(f"• Método 2: Agendador de Tarefas do Windows ({TASK_SCHEDULER_NAME})")
        print(f"• Modo: 100% Headless (Executa silenciosamente via pythonw.exe)")
        print(f"• Preset Selecionado: {preset.upper()} (Telegram, WhatsApp, ClickUp, API & Hermes)")
        print(f"• Logs em Tempo Real: 00-meta/logs/*.log")
        print("=" * 80 + "\n")
        return

    # Status
    ativo = verificar_autostart_ativo()
    if ativo:
        print(f"\n🟢 Inicialização Automática ATIVA (Inicia com o Windows).")
        print(f"• Startup VBS: {vbs_path}")
        print("As automações iniciarão em segundo plano silencioso sempre que você fizer login.\n")
    else:
        print("\n⚪ Inicialização Automática DESATIVADA.")
        print("Para ativar: python scripts/iniciar_automacoes.py autostart --install --preset all\n")


def main():
    parser = argparse.ArgumentParser(description="Orquestrador e Supervisor de Automações do Knowledge OS")
    subparsers = parser.add_subparsers(dest="acao", help="Ação a executar")

    p_run = subparsers.add_parser("run", help="Executar serviços em primeiro plano com logs unificados")
    p_run.add_argument("--all", action="store_true", help="Iniciar todos os serviços")
    p_run.add_argument("--core", action="store_true", help="Iniciar apenas o núcleo")
    p_run.add_argument("--hermes", action="store_true", help="Iniciar apenas o motor autônomo Hermes")
    p_run.add_argument("--service", "-s", help="Nome do serviço específico")

    p_start = subparsers.add_parser("start", help="Iniciar serviços em segundo plano (Headless silencioso)")
    p_start.add_argument("--all", action="store_true", help="Iniciar todos os serviços")
    p_start.add_argument("--core", action="store_true", help="Iniciar apenas o núcleo")
    p_start.add_argument("--hermes", action="store_true", help="Iniciar apenas Hermes")
    p_start.add_argument("--service", "-s", help="Nome do serviço específico")

    subparsers.add_parser("stop", help="Parar todos os serviços em segundo plano")
    subparsers.add_parser("status", help="Exibir tabela de status dos serviços")

    p_restart = subparsers.add_parser("restart", help="Reiniciar serviços em background")
    p_restart.add_argument("--all", action="store_true", help="Reiniciar todos os serviços")
    p_restart.add_argument("--core", action="store_true", help="Reiniciar apenas o núcleo")

    p_logs = subparsers.add_parser("logs", help="Visualizar logs de serviços headless")
    p_logs.add_argument("service", nargs="?", help="Nome do serviço específico (ex: telegram-bot)")
    p_logs.add_argument("-n", "--lines", type=int, default=50, help="Número de linhas a exibir")

    p_auto = subparsers.add_parser("autostart", help="Gerenciar inicialização automática no boot do Windows")
    p_auto.add_argument("--install", action="store_true", help="Instalar na inicialização do Windows (Startup)")
    p_auto.add_argument("--remove", action="store_true", help="Remover da inicialização do Windows")
    p_auto.add_argument("--status", action="store_true", help="Verificar status do autostart")
    p_auto.add_argument("--preset", default="all", choices=["all", "core", "hermes"], help="Preset de serviços para iniciar no boot")

    args = parser.parse_args()

    if args.acao == "run":
        cmd_run(args)
    elif args.acao == "start":
        cmd_start(args)
    elif args.acao == "stop":
        cmd_stop()
    elif args.acao == "status" or args.acao is None:
        cmd_status()
    elif args.acao == "restart":
        cmd_stop()
        time.sleep(1)
        cmd_start(args)
    elif args.acao == "logs":
        cmd_logs(args.service, args.lines)
    elif args.acao == "autostart":
        cmd_autostart(args.install, args.remove, args.preset)


if __name__ == "__main__":
    main()
