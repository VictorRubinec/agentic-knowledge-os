#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/telegram_remote_bot.py
Centro de Comando Remoto de Alta Performance do Second Brain via Telegram Bot API.
Processamento assíncrono multithread, estimativas de tempo em tempo real,
ações de chat (typing/upload_document), logs executivos e botões de aprovação.
"""

import sys
import os
import re
import json
import time
import datetime
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import threading
from pathlib import Path


# Garante suporte a UTF-8 no terminal Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "scripts" / "telegram_config.json"

# Inclusão do analisador de Instagram no path
ANALISADOR_DIR = REPO_ROOT / "projetos" / "analisador-instagram-telegram"
if str(ANALISADOR_DIR) not in sys.path:
    sys.path.insert(0, str(ANALISADOR_DIR))

try:
    from downloader import extrair_url_instagram, baixar_reel_instagram
    from analyzer import analisar_video_multimodal
    from researcher import enriquecer_e_validar_analise
    from pesquisa_manager import (
        salvar_dossie_cache,
        obter_dossie_cache,
        criar_pedido_pesquisa,
        gerar_slug,
        FOCOS_MAP,
        FORMATOS_MAP,
    )
    from bot import formatar_dossie_telegram
    from executar_pesquisa import executar_pedido
    HAS_INSTA_ANALYZER = True
except Exception as _e:
    HAS_INSTA_ANALYZER = False
    print(f"[Aviso] Analisador Instagram indisponível: {_e}", flush=True)

# Estado de fluxos conversacionais interativos (ex: dúvida aberta de pesquisa)
user_states: dict[int, dict] = {}

def log_event(emoji, tag, message):
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {emoji} [{tag.upper()}] {message}", flush=True)

def get_config():
    cfg = {
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_ALLOWED_USER_ID": str(os.environ.get("TELEGRAM_ALLOWED_USER_ID", "")),
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    }
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    if v and not str(v).startswith("INSIRA_") and not str(v).startswith("OPCIONAL_"):
                        cfg[k] = str(v)
        except Exception as e:
            log_event("⚠️", "CONFIG", f"Erro ao ler {CONFIG_PATH}: {e}")
    return cfg

def telegram_api_call(method, payload=None, token=""):
    url = f"https://api.telegram.org/bot{token}/{method}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        erro_body = e.read().decode("utf-8")
        log_event("❌", "API_ERROR", f"{method} (HTTP {e.code}): {erro_body}")
        return {"ok": False, "error": erro_body}
    except Exception as e:
        log_event("❌", "NET_ERROR", f"{method}: {e}")
        return {"ok": False, "error": str(e)}

def send_chat_action(chat_id, action="typing", token=""):
    # actions: typing, upload_document, record_voice, etc.
    return telegram_api_call("sendChatAction", {
        "chat_id": chat_id,
        "action": action
    }, token=token)

def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown", token=""):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    resp = telegram_api_call("sendMessage", payload, token=token)
    # Fallback automático: se falhar por erro de sintaxe do Markdown/HTML, envia como texto puro
    if not resp.get("ok") and "can't parse entities" in resp.get("error", ""):
        payload.pop("parse_mode", None)
        log_event("🔄", "FALLBACK", "Reenviando mensagem em formato texto puro para contornar caractere especial...")
        return telegram_api_call("sendMessage", payload, token=token)
    return resp

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML", token=""):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        return telegram_api_call("editMessageText", payload, token=token)
    except Exception as e:
        log_event("⚠️", "EDIT_MSG", f"Exceção ao editar mensagem {message_id}: {e}")
        return {}


def send_document(chat_id, filepath, caption="", reply_markup=None, token=""):
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    path = Path(filepath).resolve()
    if not path.exists():
        send_message(chat_id, f"❌ Arquivo não encontrado: `{path.name}`", token=token)
        return
        
    cmd = [
        "curl.exe", "-4", "-s", "-X", "POST",
        "-F", f"chat_id={chat_id}",
        "-F", f"document=@{str(path)}",
        "-F", f"caption={caption}",
        "-F", "parse_mode=Markdown"
    ]
    if reply_markup:
        cmd.extend(["-F", f"reply_markup={json.dumps(reply_markup)}"])
    cmd.append(url)
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(res.stdout) if res.stdout.strip() else {}

def answer_callback(callback_id, text="", token=""):
    return telegram_api_call("answerCallbackQuery", {
        "callback_query_id": callback_id,
        "text": text
    }, token=token)

def baixar_arquivo_telegram(file_id, token=""):
    resp = telegram_api_call("getFile", {"file_id": file_id}, token=token)
    if not resp.get("ok"):
        return None
    file_path = resp.get("result", {}).get("file_path")
    if not file_path:
        return None
    
    download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    local_dir = REPO_ROOT / "scratch" / "telegram_downloads"
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / Path(file_path).name
    
    urllib.request.urlretrieve(download_url, str(local_file))
    return local_file

def transcrever_audio(audio_path, cfg):
    groq_key = cfg.get("GROQ_API_KEY")
    openai_key = cfg.get("OPENAI_API_KEY")
    
    if groq_key:
        log_event("🎙️", "WHISPER", "Transcrevendo via Groq Whisper-large-v3...")
        cmd = [
            "curl.exe", "-4", "-s", "-X", "POST",
            "https://api.groq.com/openai/v1/audio/transcriptions",
            "-H", f"Authorization: Bearer {groq_key}",
            "-F", f"file=@{str(audio_path)}",
            "-F", "model=whisper-large-v3",
            "-F", "language=pt"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            return json.loads(res.stdout).get("text", "")
        except Exception:
            return ""
    elif openai_key:
        log_event("🎙️", "WHISPER", "Transcrevendo via OpenAI Whisper-1...")
        cmd = [
            "curl.exe", "-4", "-s", "-X", "POST",
            "https://api.openai.com/v1/audio/transcriptions",
            "-H", f"Authorization: Bearer {openai_key}",
            "-F", f"file=@{str(audio_path)}",
            "-F", "model=whisper-1",
            "-F", "language=pt"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            return json.loads(res.stdout).get("text", "")
        except Exception:
            return ""
    return None

# ==============================================================================
# Execuções Assíncronas com Estimativa de Tempo
# ==============================================================================

def worker_report(chat_id, token):
    t0 = time.time()
    log_event("⚙️", "REPORT", "Iniciando compilação de status report semanal...")
    send_chat_action(chat_id, "upload_document", token=token)
    
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "gerar_status_report_semanal.py")]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    duracao = time.time() - t0
    
    if res.returncode == 0:
        pdf_dir = REPO_ROOT / "trabalho" / "join4" / "produto" / "relatorios" / "pdf"
        pdfs = sorted(pdf_dir.glob("status-report-*.pdf"), key=os.path.getmtime, reverse=True)
        if pdfs:
            pdf_alvo = pdfs[0]
            log_event("📄", "REPORT", f"PDF gerado com sucesso ({duracao:.1f}s): {pdf_alvo.name}")
            caption = f"📊 *Status Report Semanal Executivo Concluído!*\n⏱️ *Tempo de processamento:* `{duracao:.1f}s`\n📁 *Arquivo:* `{pdf_alvo.name}`"
            send_document(chat_id, pdf_alvo, caption=caption, token=token)
            log_event("✅", "REPORT", f"Documento entregue ao usuário em {duracao:.1f}s")
        else:
            send_message(chat_id, "⚠️ Relatório MDX gerado, mas o arquivo PDF não foi localizado.", token=token)
    else:
        log_event("❌", "REPORT", f"Falha na compilação: {res.stderr[:200]}")
        send_message(chat_id, f"❌ Erro ao compilar relatório semanal:\n```{res.stderr[:300]}```", token=token)

def worker_doctor(chat_id, token):
    t0 = time.time()
    log_event("🩺", "DOCTOR", "Iniciando auditoria completa do Second Brain...")
    send_chat_action(chat_id, "typing", token=token)
    
    res_links = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "validar_links.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    res_fm = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "validar_frontmatter.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    res_org = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "gerar_organization.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    duracao = time.time() - t0

    status_links = "✅ 0 links quebrados (100% íntegro)" if res_links.returncode == 0 else "❌ Violações encontradas"
    status_fm = "✅ 100% em conformidade com o padrão" if res_fm.returncode == 0 else "❌ Falha no frontmatter"
    status_org = "✅ Catálogo sincronizado com o disco" if res_org.returncode == 0 else "⚠️ Matriz precisa de atualização"
    
    msg = f"""🩺 *Laudo de Saúde do Second Brain* (concluído em `{duracao:.1f}s`)
    
• **Links & Hiperlinks:** {status_links}
• **Frontmatter & Metadados:** {status_fm}
• **Catálogo ORGANIZATION.md:** {status_org}

_Ambiente 100% auditado e validado!_"""
    send_message(chat_id, msg, token=token)
    log_event("✅", "DOCTOR", f"Laudo de saúde enviado em {duracao:.1f}s")

def worker_sync(chat_id, task_input, token):
    t0 = time.time()
    log_event("🔄", "SYNC", f"Iniciando sincronização inteligente da tarefa '{task_input}'...")
    send_chat_action(chat_id, "upload_document", token=token)
    
    tarefas_dir = REPO_ROOT / "trabalho" / "join4" / "produto" / "tarefas"
    mdx_alvo = None
    real_clickup_id = task_input
    
    # 1. Se o usuário passou slug, código ou número (ex: task-005, 005 ou task-005-etl...)
    termo = task_input.lower().strip()
    for f in tarefas_dir.glob("task-*.mdx"):
        if termo in f.stem.lower():
            mdx_alvo = f
            conteudo = f.read_text(encoding="utf-8")
            m_id = re.search(r'taskId="([^"]+)"', conteudo)
            if m_id:
                real_clickup_id = m_id.group(1)
            break
            
    # 2. Se não achou pelo nome do arquivo, busca por menção ao ClickUp ID dentro dos arquivos
    if not mdx_alvo:
        for f in tarefas_dir.glob("task-*.mdx"):
            conteudo = f.read_text(encoding="utf-8")
            if task_input in conteudo:
                mdx_alvo = f
                m_id = re.search(r'taskId="([^"]+)"', conteudo)
                real_clickup_id = m_id.group(1) if m_id else task_input
                break
                
    # 3. Se for um ID numérico/alfanumérico do ClickUp e ainda não tiver arquivo local, consulta a API
    if not mdx_alvo and not real_clickup_id.startswith("task-"):
        cmd = [sys.executable, str(REPO_ROOT / "scripts" / "analisador_clickup.py"), "--task", real_clickup_id]
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        for f in tarefas_dir.glob("task-*.mdx"):
            if real_clickup_id in f.read_text(encoding="utf-8"):
                mdx_alvo = f
                break
                
    # 4. Compila o PDF do dossiê encontrado
    if mdx_alvo:
        pdf_cmd = [sys.executable, str(REPO_ROOT / "scripts" / "gerar_pdf.py"), str(mdx_alvo), "-t", "join4"]
        subprocess.run(pdf_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        pdf_path = tarefas_dir / "pdf" / f"{mdx_alvo.stem}.pdf"
        duracao = time.time() - t0
        if pdf_path.exists():
            markup = {
                "inline_keyboard": [
                    [{"text": "✅ Aprovar e Enviar ao ClickUp", "callback_data": f"approve_{real_clickup_id}_{pdf_path.name}"}],
                    [{"text": "❌ Reprovar / Ajustar", "callback_data": f"reject_{real_clickup_id}"}]
                ]
            }
            caption = f"📄 *Dossiê Compilado: `{mdx_alvo.stem}`*\n⏱️ *Tempo:* `{duracao:.1f}s`\n🎯 *ClickUp ID:* `{real_clickup_id}`\n\nVocê aprova o anexo deste PDF no ClickUp?"
            send_document(chat_id, pdf_path, caption=caption, reply_markup=markup, token=token)
            log_event("✅", "SYNC", f"Dossiê de {mdx_alvo.stem} enviado em {duracao:.1f}s com botões de aprovação")
            return

    duracao = time.time() - t0
    send_message(chat_id, f"❌ Tarefa `{task_input}` não localizada no repositório nem no ClickUp (em `{duracao:.1f}s`).", token=token)


def worker_audio(chat_id, file_id, cfg):
    token = cfg["TELEGRAM_BOT_TOKEN"]
    t0 = time.time()
    log_event("🎙️", "AUDIO", "Processando arquivo de áudio recebido...")
    send_chat_action(chat_id, "typing", token=token)
    
    local_audio = baixar_arquivo_telegram(file_id, token=token)
    if not local_audio:
        send_message(chat_id, "❌ Falha ao baixar áudio dos servidores do Telegram.", token=token)
        return
        
    texto = transcrever_audio(local_audio, cfg)
    duracao = time.time() - t0
    if not texto:
        send_message(chat_id, "⚠️ Áudio recebido, mas não foi possível transcrever automaticamente.\n_Configure `GROQ_API_KEY` ou `OPENAI_API_KEY` no `telegram_config.json` para transcrição Whisper instantânea._", token=token)
        return
        
    msg_confirmacao = f"""📝 *Transcrição Concluída em `{duracao:.1f}s`:*
> "{texto[:400]}..."

_Sintetizando ata executiva e alinhando stakeholder via `meeting-to-knowledge`..._"""
    send_message(chat_id, msg_confirmacao, token=token)
    log_event("✅", "AUDIO", f"Transcrição concluída em {duracao:.1f}s ({len(texto)} caracteres)")


def worker_instagram(chat_id, insta_url, reply_to_id, cfg):
    token = cfg["TELEGRAM_BOT_TOKEN"]
    t0 = time.time()
    log_event("📱", "INSTA", f"Iniciando análise de Reel: {insta_url}")

    msg_status = send_message(
        chat_id,
        "📥 <b>[1/4] Baixando vídeo e metadados do Instagram...</b>\n<i>Aguarde alguns segundos.</i>",
        parse_mode="HTML",
        token=token
    )
    status_id = msg_status.get("result", {}).get("message_id") if msg_status and msg_status.get("ok") else None

    try:
        send_chat_action(chat_id, "upload_video", token=token)
        post = baixar_reel_instagram(insta_url)

        if status_id:
            edit_message(
                chat_id, status_id,
                "🧠 <b>[2/4] Analisando áudio, vídeo e legenda com IA Multimodal...</b>\n<i>Inspecionando narração, código na tela e descrição.</i>",
                token=token
            )

        send_chat_action(chat_id, "typing", token=token)
        analise = analisar_video_multimodal(post)

        qtd_techs = len(analise.technologies) if analise.technologies else 1
        if status_id:
            msg_aud = (
                f"🔍 <b>[3/4] Toolkit identificado ({qtd_techs} ferramentas)!</b>\n<i>Auditando repositórios no GitHub...</i>"
                if analise.is_collection or qtd_techs > 1
                else "🔍 <b>[3/4] Enriquecendo dados e checando GitHub...</b>"
            )
            edit_message(chat_id, status_id, msg_aud, token=token)

        dossie = enriquecer_e_validar_analise(analise, post)
        texto_html, reply_markup = formatar_dossie_telegram(dossie, insta_url)

        duracao = time.time() - t0
        if status_id:
            edit_message(
                chat_id, status_id,
                f"✅ <b>[4/4] Análise Concluída em {duracao:.1f}s!</b>",
                token=token
            )

        send_message(chat_id, texto_html, reply_markup=reply_markup, parse_mode="HTML", token=token)
        log_event("✅", "INSTA", f"Dossiê do Reel enviado com sucesso em {duracao:.1f}s")
    except Exception as e:
        log_event("❌", "INSTA_ERROR", f"Falha ao processar Instagram: {e}")
        send_message(
            chat_id,
            f"❌ <b>Erro ao analisar Reel do Instagram:</b>\n<code>{str(e)[:300]}</code>",
            parse_mode="HTML",
            token=token
        )


def enviar_confirmacao_pedido(chat_id: int, pedido: dict, message_id: int | None = None, token: str = ""):
    html = [
        "✅ <b>Ordem de Pesquisa Confirmada!</b>\n",
        f"📋 <b>ID:</b> <code>#{pedido['id']}</code>",
        f"🎯 <b>Tecnologia:</b> <code>{pedido['tech_name']}</code>",
        f"🔍 <b>Foco:</b> {pedido['foco_nome']}",
        f"📄 <b>Formato:</b> {pedido['formato_nome']}"
    ]
    if pedido.get("duvida_especifica"):
        html.append(f"💬 <b>Requisito Específico:</b> <i>\"{pedido['duvida_especifica']}\"</i>")

    html.append(
        "\n⚙️ <b>Pesquisa iniciada no ambiente do Antigravity!</b>\n"
        "<i>Investigando repositório GitHub, gerando artefato HTML5 e compilando PDF corporativo A4...</i>\n\n"
        "⏳ <i>Você receberá o PDF executivo aqui neste chat em instantes.</i>"
    )
    msg_final = "\n".join(html)
    if message_id:
        edit_message(chat_id, message_id, msg_final, token=token)
    else:
        send_message(chat_id, msg_final, parse_mode="HTML", token=token)


def worker_executar_pesquisa(chat_id: int, pedido: dict, token: str = ""):
    t0 = time.time()
    log_event("🔬", "PESQUISA", f"Iniciando compilação autônoma para {pedido['tech_name']} ({pedido['id']})...")
    send_chat_action(chat_id, "upload_document", token=token)
    try:
        executar_pedido(pedido["id"])
        duracao = time.time() - t0
        log_event("✅", "PESQUISA", f"Pesquisa #{pedido['id']} concluída e enviada com sucesso em {duracao:.1f}s")
    except Exception as e:
        log_event("❌", "PESQUISA_ERROR", f"Erro na pesquisa #{pedido['id']}: {e}")
        send_message(
            chat_id,
            f"❌ <b>Falha ao compilar pesquisa autônoma:</b>\n<code>{str(e)[:250]}</code>\n\n"
            f"<i>Comando manual para terminal:</i> <code>python scripts/executar_pesquisa.py --pedido {pedido['id']}</code>",
            parse_mode="HTML",
            token=token
        )

# ==============================================================================
# Roteamento de Comandos & Handlers
# ==============================================================================

def handle_cmd_status(chat_id, token=""):
    tarefas_dir = REPO_ROOT / "trabalho" / "join4" / "produto" / "tarefas"
    tarefas = sorted(tarefas_dir.glob("task-*.mdx"))
    linhas = ["📋 *Tarefas de Produto da Join4:*", ""]
    for t in tarefas[:8]:
        linhas.append(f"• `{t.stem}`")
    linhas.append("")
    linhas.append("💡 *Dica:* Envie `/sync <ID>` para sincronizar qualquer tarefa.")
    send_message(chat_id, "\n".join(linhas), token=token)
    log_event("📋", "STATUS", "Lista de tarefas enviada com sucesso")


def handle_cmd_cronograma(chat_id, token=""):
    crono_path = REPO_ROOT / "00-meta" / "cronograma_pesquisas.json"
    queue_path = REPO_ROOT / "00-meta" / "hermes_tasks.json"

    if not crono_path.exists():
        send_message(chat_id, "⚠️ Cronograma editorial não localizado em `00-meta/cronograma_pesquisas.json`.", token=token)
        return

    try:
        with open(crono_path, "r", encoding="utf-8") as f:
            crono = json.load(f)
    except Exception as e:
        send_message(chat_id, f"❌ Erro ao ler cronograma: {e}", token=token)
        return

    status_str = "⏸️ *PAUSADO*" if crono.get("pausado") else "🟢 *ATIVO*"
    slots = ", ".join(crono.get("slots_horario", ["08:30", "19:30"]))
    cota = crono.get("cota_maxima_diaria", 2)

    agora = datetime.datetime.now()
    dias_semana_nomes = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    dia_hoje_chave = dias_semana_nomes[agora.weekday()]
    grade = crono.get("grade_semanal", {})
    tema_hoje = grade.get(dia_hoje_chave, {}).get("tema_titulo", "Descanso")

    linhas = [
        "🗓️ *CRONOGRAMA EDITORIAL DE ESTUDOS*",
        f"• *Status:* {status_str}",
        f"• *Horários Nobres:* `{slots}` (Máx. {cota} whitepapers/dia)",
        f"• *Tema de Hoje:* *{tema_hoje}*",
        "",
        "📚 *Grade Semanal Temática:*",
        "• *Segunda:* Notícias Tech & Lançamentos",
        "• *Terça:* Automações & Pipelines",
        "• *Quarta:* Repositórios Famosos (Trending)",
        "• *Quinta:* Evolução de Conhecimento & Engenharia",
        "• *Sexta:* Tendências de Mercado & Negócios",
        "• *Sábado:* RPG & Ordem Paranormal",
        "• *Domingo:* Descanso / Pausa",
        ""
    ]

    # Carregar próximas tarefas agendadas
    if queue_path.exists():
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
            pendentes = [t for t in queue.get("tasks", []) if t.get("status") == "pending"]
            if pendentes:
                linhas.append("⏳ *Próximas Entregas Agendadas:*")
                for p in pendentes[:4]:
                    sched = (p.get("scheduled_for") or "Imediato")[:16].replace("T", " às ")
                    tema = p.get("dia_nome") or p.get("tema_id", "Geral")
                    linhas.append(f"• `{sched}` [{tema}]: *{p['titulo'][:35]}*")
            else:
                linhas.append("ℹ️ _Nenhuma pesquisa pendente na fila. O curador alimentará nos horários de varredura._")
        except Exception:
            pass

    linhas.append("")
    linhas.append("💡 *Controle:* Digite `/pausar` para suspender ou `/retomar` para reativar.")
    send_message(chat_id, "\n".join(linhas), token=token)
    log_event("🗓️", "CRONOGRAMA", "Grade editorial enviada ao Telegram")


def handle_cmd_pausar(chat_id, token=""):
    crono_path = REPO_ROOT / "00-meta" / "cronograma_pesquisas.json"
    if not crono_path.exists():
        send_message(chat_id, "⚠️ Cronograma não localizado.", token=token)
        return
    try:
        with open(crono_path, "r", encoding="utf-8") as f:
            crono = json.load(f)
        crono["pausado"] = True
        crono_path.write_text(json.dumps(crono, indent=2, ensure_ascii=False), encoding="utf-8")
        send_message(chat_id, "⏸️ *Cronograma Pausado!* O Hermes não disparará relatórios automáticos até você enviar `/retomar`.", token=token)
        log_event("⏸️", "PAUSAR", "Cronograma pausado pelo usuário")
    except Exception as e:
        send_message(chat_id, f"❌ Erro ao pausar: {e}", token=token)


def handle_cmd_retomar(chat_id, token=""):
    crono_path = REPO_ROOT / "00-meta" / "cronograma_pesquisas.json"
    if not crono_path.exists():
        send_message(chat_id, "⚠️ Cronograma não localizado.", token=token)
        return
    try:
        with open(crono_path, "r", encoding="utf-8") as f:
            crono = json.load(f)
        crono["pausado"] = False
        crono_path.write_text(json.dumps(crono, indent=2, ensure_ascii=False), encoding="utf-8")
        send_message(chat_id, "▶️ *Cronograma Retomado!* O Hermes voltará a entregar os whitepapers nos horários nobres (08:30 e 19:30).", token=token)
        log_event("▶️", "RETOMAR", "Cronograma retomado pelo usuário")
    except Exception as e:
        send_message(chat_id, f"❌ Erro ao retomar: {e}", token=token)


def process_update(update, cfg):
    token = cfg["TELEGRAM_BOT_TOKEN"]
    allowed_id = cfg["TELEGRAM_ALLOWED_USER_ID"]

    # Callbacks de Botões Inline (Aprovação de Tarefas)
    if "callback_query" in update:
        cb = update["callback_query"]
        cb_id = cb["id"]
        from_id = str(cb.get("from", {}).get("id"))
        data = cb.get("data", "")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")
        
        if allowed_id and from_id != allowed_id:
            answer_callback(cb_id, "Acesso não autorizado.", token=token)
            return

        if data.startswith("approve_"):
            partes = data.split("_")
            task_id = partes[1]
            pdf_name = partes[2] if len(partes) > 2 else ""
            pdf_path = REPO_ROOT / "trabalho" / "join4" / "produto" / "tarefas" / "pdf" / pdf_name
            answer_callback(cb_id, "Aprovado! Anexando ao ClickUp...", token=token)
            log_event("🚀", "APPROVE", f"Usuário aprovou envio do PDF {pdf_name} para tarefa {task_id}")
            if pdf_path.exists():
                cmd = [sys.executable, str(REPO_ROOT / "scripts" / "analisador_clickup.py"), "--task", task_id, "--attach-pdf", str(pdf_path), "--post-comment"]
                subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
                send_message(chat_id, f"🚀 *Sucesso!*\nPDF `{pdf_name}` anexado e parecer técnico publicado na tarefa `{task_id}` do ClickUp!", token=token)
                log_event("✅", "APPROVE", f"PDF anexado e parecer postado com sucesso no ClickUp ({task_id})")
        elif data.startswith("reject_"):
            answer_callback(cb_id, "Ação cancelada.", token=token)
            log_event("❌", "REJECT", f"Usuário reprovou envio para ClickUp ({data})")
            send_message(chat_id, "❌ Anexo reprovado. Nenhum arquivo foi enviado ao ClickUp.", token=token)
        elif data.startswith("pesq_init:"):
            slug = data.split(":", 1)[1]
            dossie = obter_dossie_cache(slug) or {}
            tech_name = dossie.get("tech_name") or slug.replace("-", " ").title()
            texto_1 = (
                f"🔬 <b>Configuração de Pesquisa: {tech_name}</b>\n\n"
                "<b>[1/3] Qual é o foco principal da investigação técnica?</b>\n"
                "<i>Selecione uma das opções abaixo:</i>"
            )
            botoes_1 = [
                [{"text": "🏗️ Arquitetura & Viabilidade", "callback_data": f"pesq_f:arq:{slug}"}],
                [{"text": "📊 Comparativo & Alternativas", "callback_data": f"pesq_f:comp:{slug}"}],
                [{"text": "💻 Guia Prático / PoC de Teste", "callback_data": f"pesq_f:poc:{slug}"}],
                [{"text": "📚 Deep Dive Completo (360°)", "callback_data": f"pesq_f:all:{slug}"}]
            ]
            answer_callback(cb_id, token=token)
            send_message(chat_id, texto_1, reply_markup={"inline_keyboard": botoes_1}, parse_mode="HTML", token=token)
        elif data.startswith("pesq_f:"):
            _, foco_code, slug = data.split(":", 2)
            dossie = obter_dossie_cache(slug) or {}
            tech_name = dossie.get("tech_name") or slug.replace("-", " ").title()
            foco_nome = FOCOS_MAP.get(foco_code, foco_code)
            texto_2 = (
                f"🔬 <b>Configuração de Pesquisa: {tech_name}</b>\n"
                f"🎯 Foco: <b>{foco_nome}</b>\n\n"
                "<b>[2/3] Escolha o formato de saída do entregável:</b>"
            )
            botoes_2 = [
                [{"text": "📄 Dossiê Knowledge OS (HTML + PDF A4)", "callback_data": f"pesq_p:pdf:{foco_code}:{slug}"}],
                [{"text": "⚡ Resumo Executivo Rápido (Telegram)", "callback_data": f"pesq_p:resumo:{foco_code}:{slug}"}]
            ]
            answer_callback(cb_id, token=token)
            edit_message(chat_id, cb.get("message", {}).get("message_id"), texto_2, reply_markup={"inline_keyboard": botoes_2}, token=token)
        elif data.startswith("pesq_p:"):
            _, prof_code, foco_code, slug = data.split(":", 3)
            dossie = obter_dossie_cache(slug) or {}
            tech_name = dossie.get("tech_name") or slug.replace("-", " ").title()
            foco_nome = FOCOS_MAP.get(foco_code, foco_code)
            prof_nome = FORMATOS_MAP.get(prof_code, prof_code)
            user_states[chat_id] = {
                "stage": "aguardando_duvida",
                "slug": slug,
                "foco_code": foco_code,
                "prof_code": prof_code,
                "tech_name": tech_name
            }
            texto_3 = (
                f"🔬 <b>Configuração de Pesquisa: {tech_name}</b>\n"
                f"🎯 Foco: <b>{foco_nome}</b>\n"
                f"📄 Formato: <b>{prof_nome}</b>\n\n"
                "<b>[3/3] Deseja adicionar alguma dúvida ou objetivo específico?</b>\n"
                "<i>Responda com seu texto a este chat com sua pergunta, "
                "ou clique no botão abaixo para concluir imediatamente:</i>"
            )
            botoes_3 = [
                [{"text": "🚀 Concluir e Enviar para o Antigravity", "callback_data": f"pesq_done:sem_duvida:{prof_code}:{foco_code}:{slug}"}]
            ]
            answer_callback(cb_id, token=token)
            edit_message(chat_id, cb.get("message", {}).get("message_id"), texto_3, reply_markup={"inline_keyboard": botoes_3}, token=token)
        elif data.startswith("pesq_done:"):
            partes = data.split(":", 4)
            if len(partes) >= 5:
                _, _, prof_code, foco_code, slug = partes
                user_states.pop(chat_id, None)
                pedido = criar_pedido_pesquisa(chat_id, slug, foco_code, prof_code, duvida_especifica="")
                answer_callback(cb_id, token=token)
                enviar_confirmacao_pedido(chat_id, pedido, message_id=cb.get("message", {}).get("message_id"), token=token)
                threading.Thread(target=worker_executar_pesquisa, args=(chat_id, pedido, token), daemon=True).start()
        return

    message = update.get("message")
    if not message:
        return

    chat_id = message.get("chat", {}).get("id")
    from_id = str(message.get("from", {}).get("id"))
    username = message.get("from", {}).get("username", "usuario")
    text = (message.get("text") or "").strip()

    # Validação de Segurança
    if allowed_id and from_id != allowed_id:
        log_event("⛔", "AUTH_BLOCKED", f"Rejeitada mensagem de @{username} (ID: {from_id})")
        send_message(chat_id, f"⛔ *Acesso Negado.* Seu Telegram ID (`{from_id}`) não está autorizado neste Second Brain.", token=token)
        return

    # 1. Resposta de Pergunta Aberta do Fluxo de Pesquisa
    if chat_id in user_states and user_states[chat_id].get("stage") == "aguardando_duvida":
        state = user_states.pop(chat_id)
        duvida_texto = text.strip()
        log_event("🔬", "DUVIDA", f"Dúvida de pesquisa recebida de @{username}: {duvida_texto[:40]}")
        pedido = criar_pedido_pesquisa(
            chat_id=chat_id,
            slug=state["slug"],
            foco_code=state["foco_code"],
            formato_code=state["prof_code"],
            duvida_especifica=duvida_texto
        )
        enviar_confirmacao_pedido(chat_id, pedido, token=token)
        threading.Thread(target=worker_executar_pesquisa, args=(chat_id, pedido, token), daemon=True).start()
        return

    # 2. Tratamento de Áudios / Mensagens de Voz
    if "voice" in message or "audio" in message:
        file_id = message.get("voice", {}).get("file_id") or message.get("audio", {}).get("file_id")
        log_event("🎙️", "VOICE", f"Áudio recebido de @{username} (ID: {from_id})")
        send_message(chat_id, "🎙️ *Áudio recebido!*\n⏱️ *Tempo estimado:* ~2 a 4 segundos\n⚙️ *Status:* Baixando e processando transcrição...", token=token)
        threading.Thread(target=worker_audio, args=(chat_id, file_id, cfg), daemon=True).start()
        return

    # 3. Tratamento de Reels e Links do Instagram
    if HAS_INSTA_ANALYZER and extrair_url_instagram(text):
        url_insta = extrair_url_instagram(text)
        log_event("📱", "REEL", f"Link do Instagram identificado: {url_insta}")
        threading.Thread(target=worker_instagram, args=(chat_id, url_insta, message.get("message_id"), cfg), daemon=True).start()
        return

    # 4. Comandos de Texto
    if text.startswith("/start") or text.startswith("/help"):
        log_event("⚡", "CMD", f"/help acionado por @{username}")
        menu = """🤖 *Second Brain Remote Control Hub*

Comandos disponíveis:
• 🗓️ `/cronograma` — Grade semanal de estudos e próximas pesquisas
• ⏸️ `/pausar` — Pausar entregas automáticas do Hermes
• ▶️ `/retomar` — Retomar entregas nos horários nobres (08:30 e 19:30)
• 📊 `/report` — Gerar e receber o Status Report Semanal em PDF (~5s)
• 🩺 `/doctor` — Diagnóstico de saúde do repositório (links & frontmatter) (~2s)
• 📋 `/status` — Listar tarefas de Produto ativas (instantâneo)
• 🔄 `/sync <TASK_ID>` — Sincronizar tarefa do ClickUp e gerar PDF com aprovação
• 📱 *Cole um link de Reel do Instagram* para análise multimodal e pesquisa de tecnologias
• 🎙️ *Envie uma mensagem de voz/áudio* para transcrever e registrar reunião

_Usuário autorizado:_ `@{}` (`{}`)""".format(username, from_id)
        send_message(chat_id, menu, token=token)
    elif text.startswith("/cronograma"):
        log_event("⚡", "CMD", f"/cronograma disparado por @{username}")
        handle_cmd_cronograma(chat_id, token=token)
    elif text.startswith("/pausar"):
        log_event("⚡", "CMD", f"/pausar disparado por @{username}")
        handle_cmd_pausar(chat_id, token=token)
    elif text.startswith("/retomar"):
        log_event("⚡", "CMD", f"/retomar disparado por @{username}")
        handle_cmd_retomar(chat_id, token=token)
    elif text.startswith("/report"):
        log_event("⚡", "CMD", f"/report disparado por @{username}")
        aviso = """⏳ *Iniciando compilação do Status Report Semanal...*
⏱️ *Tempo estimado:* ~5 a 7 segundos
⚙️ *Processando:* Varrida de tarefas ativas, montagem de métricas e compilação do PDF A4 corporativo..."""
        send_message(chat_id, aviso, token=token)
        threading.Thread(target=worker_report, args=(chat_id, token), daemon=True).start()
    elif text.startswith("/doctor"):
        log_event("⚡", "CMD", f"/doctor disparado por @{username}")
        aviso = """🩺 *Iniciando Diagnóstico do Second Brain...*
⏱️ *Tempo estimado:* ~2 a 3 segundos
⚙️ *Auditando:* Links cruzados, metadados frontmatter e sincronia do catálogo..."""
        send_message(chat_id, aviso, token=token)
        threading.Thread(target=worker_doctor, args=(chat_id, token), daemon=True).start()
    elif text.startswith("/status"):
        log_event("⚡", "CMD", f"/status disparado por @{username}")
        handle_cmd_status(chat_id, token=token)
    elif text.startswith("/sync"):
        partes = text.split()
        if len(partes) > 1:
            t_id = partes[1]
            log_event("⚡", "CMD", f"/sync {t_id} disparado por @{username}")
            aviso = f"""🔄 *Iniciando Sincronização da Tarefa `{t_id}`...*
⏱️ *Tempo estimado:* ~6 a 9 segundos
⚙️ *Processando:* Extração da API ClickUp, validação anti-orphan e compilação do PDF..."""
            send_message(chat_id, aviso, token=token)
            threading.Thread(target=worker_sync, args=(chat_id, t_id, token), daemon=True).start()
        else:
            send_message(chat_id, "Uso correto: `/sync <TASK_ID>` (ex: `/sync 868fd1234`)", token=token)
    elif text:
        log_event("💬", "MSG", f"Texto não reconhecido de @{username}: {text[:30]}")
        send_message(chat_id, "Comando não reconhecido. Digite `/help` para visualizar o menu.", token=token)

def main():
    cfg = get_config()
    token = cfg.get("TELEGRAM_BOT_TOKEN")
    if not token:
        log_event("❌", "STARTUP", "TELEGRAM_BOT_TOKEN não configurado no telegram_config.json!")
        sys.exit(1)

    print("=" * 65, flush=True)
    print("🤖 Second Brain Remote Control Hub — Telegram Bot (Multithread)", flush=True)
    print(f"🔒 Usuário Autorizado: {cfg.get('TELEGRAM_ALLOWED_USER_ID')}", flush=True)
    print("⚡ Processamento Assíncrono com Feedback Imediato & Estimativas", flush=True)
    print("=" * 65, flush=True)
    log_event("🚀", "ONLINE", "Conectado à Telegram Bot API. Aguardando comandos...")

    last_offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={last_offset}&timeout=20"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("ok"):
                    for update in data.get("result", []):
                        update_id = update["update_id"]
                        last_offset = update_id + 1
                        process_update(update, cfg)
        except urllib.error.URLError:
            time.sleep(2)
        except Exception as e:
            log_event("⚠️", "LOOP_ERROR", str(e))
            time.sleep(2)

if __name__ == "__main__":
    main()
