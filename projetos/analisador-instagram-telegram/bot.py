#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/bot.py — Bot Telegram para Análise Multimodal de Reels do Instagram
"""

import sys
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import aiohttp

# Configuração de encoding para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ALLOWED_USER_ID,
    validar_configuracoes
)
from downloader import baixar_reel_instagram, extrair_url_instagram, InstagramPost
from analyzer import analisar_video_multimodal, MultimodalReelAnalysis
from researcher import (
    enriquecer_e_validar_analise,
    enriquecer_e_validar_tecnologia,
    ValidatedTechnologyDossier,
    ValidatedCollectionDossier
)
from pesquisa_manager import (
    salvar_dossie_cache,
    obter_dossie_cache,
    criar_pedido_pesquisa,
    gerar_slug,
    FOCOS_MAP,
    FORMATOS_MAP
)

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
from executar_pesquisa import executar_pedido

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("telegram_bot")

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
executor = ThreadPoolExecutor(max_workers=3)


def formatar_dossie_telegram(dossier: ValidatedCollectionDossier | ValidatedTechnologyDossier, original_url: str) -> tuple[str, dict | None]:
    """
    Formata o dossiê executivo para mensagem rica no Telegram em HTML com botões inline.
    Distingue entre ferramenta única e compilações/toolkits multi-tecnologias (1:N).
    Salva também o dossiê e seus itens em cache para os fluxos interativos de pesquisa.
    """
    # 1. Caso seja Toolkit ou Coleção com múltiplas ferramentas (1:N)
    if isinstance(dossier, ValidatedCollectionDossier) and (dossier.is_collection or len(dossier.items) > 1):
        col_slug = gerar_slug(dossier.collection_title)
        salvar_dossie_cache(col_slug, dossier, original_url)

        total_items = len(dossier.items)
        emojis_num = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        html = []
        html.append(f"📦 <b>TOOLKIT / COMPILAÇÃO IDENTIFICADA:</b> <code>{dossier.collection_title}</code> ({total_items} Ferramentas)\n")
        if dossier.collection_overview:
            html.append(f"💡 <b>VISÃO GERAL DO ECOSSISTEMA:</b>\n{dossier.collection_overview}\n")

        html.append("🛠️ <b>FERRAMENTAS IDENTIFICADAS NO VÍDEO:</b>")
        for i, item in enumerate(dossier.items):
            num = emojis_num[i] if i < len(emojis_num) else f"[{i+1}]"
            stars_part = f" (⭐ {item.stars_display} stars | {item.language})" if item.repo_found else ""
            repo_part = f" — <a href=\"{item.repo_url}\">{item.repo_name}</a>" if (item.repo_found and item.repo_url) else ""
            html.append(f"\n{num} <b>{item.tech_name}</b>{stars_part}{repo_part}")
            html.append(f"• <b>O que faz:</b> {item.summary}")
            if item.install_command:
                html.append(f"• <b>Comando:</b> <code>{item.install_command}</code>")

        texto_final = "\n".join(html)

        # Montagem do Teclado com botões individuais por ferramenta
        botoes = []
        linha_atual = []
        for i, item in enumerate(dossier.items):
            num = emojis_num[i] if i < len(emojis_num) else f"{i+1}"
            it_slug = gerar_slug(item.tech_name)
            rotulo = f"{num} Pesquisar {item.tech_name[:14]}"
            linha_atual.append({"text": rotulo, "callback_data": f"pesq_init:{it_slug}"})
            if len(linha_atual) == 2:
                botoes.append(linha_atual)
                linha_atual = []
        if linha_atual:
            botoes.append(linha_atual)

        # Botão principal em destaque: Pesquisa do Toolkit Completo
        botoes.append([{"text": f"📚 Pesquisar Toolkit Completo ({total_items}-em-1)", "callback_data": f"pesq_init:{col_slug}"}])
        # Link do Reel no Instagram
        botoes.append([{"text": "📱 Ver Reel no Instagram", "url": original_url}])

        return texto_final, {"inline_keyboard": botoes}

    # 2. Caso seja Ferramenta Única (ou coleção contendo exatamente 1 item)
    item_unico = dossier.items[0] if (isinstance(dossier, ValidatedCollectionDossier) and dossier.items) else dossier
    slug = gerar_slug(item_unico.tech_name)
    salvar_dossie_cache(slug, item_unico, original_url)

    html = []
    html.append(f"🔍 <b>TECNOLOGIA IDENTIFICADA:</b> <code>{item_unico.tech_name}</code>\n")

    if item_unico.repo_found:
        html.append(f"📦 <b>Repositório:</b> <a href=\"{item_unico.repo_url}\">{item_unico.repo_name}</a>")
        html.append(f"⭐ <b>Métricas:</b> {item_unico.stars_display} stars | {item_unico.forks} forks | {item_unico.language}")
        html.append(f"📜 <b>Licença:</b> {item_unico.license_name} | 🕒 <b>Atualizado:</b> {item_unico.last_update_str}\n")

    if item_unico.official_website:
        html.append(f"🌐 <b>Website / Docs:</b> <a href=\"{item_unico.official_website}\">{item_unico.official_website}</a>\n")

    html.append(f"💡 <b>O QUE É E O QUE RESOLVE:</b>\n{item_unico.summary}\n")

    html.append("📺 <b>DESTAQUES DA PERCEPÇÃO TRIPLA:</b>")
    html.append(f"• <b>Áudio:</b> {item_unico.audio_insights}")
    html.append(f"• <b>Vídeo/Tela:</b> {item_unico.video_insights}\n")

    if item_unico.install_command:
        html.append(f"⚙️ <b>GUIA DE INÍCIO RÁPIDO:</b>\n<code>{item_unico.install_command}</code>\n")

    html.append(f"⚖️ <b>VEREDITO TÉCNICO:</b>\n<i>{item_unico.verdict}</i>")

    texto_final = "\n".join(html)

    # Montagem do Inline Keyboard
    botoes = []
    botoes.append([{"text": "🔬 Gerar Pesquisa no Antigravity", "callback_data": f"pesq_init:{slug}"}])

    linha_links = []
    if item_unico.repo_found and item_unico.repo_url:
        linha_links.append({"text": "⭐ GitHub", "url": item_unico.repo_url})
    if item_unico.official_website:
        linha_links.append({"text": "📖 Docs / Site", "url": item_unico.official_website})
    if linha_links:
        botoes.append(linha_links)

    botoes.append([{"text": "📱 Ver Reel no Instagram", "url": original_url}])

    reply_markup = {"inline_keyboard": botoes} if botoes else None
    return texto_final, reply_markup


class TelegramBotService:
    """Serviço de escuta e processamento de mensagens e callbacks do Telegram."""

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.last_update_id = 0
        self.user_states: dict[int, dict] = {}

    async def start(self):
        self.session = aiohttp.ClientSession()
        logger.info("Bot do Telegram conectado e aguardando links de Reels e pesquisas...")

        while True:
            try:
                updates = await self.get_updates()
                for update in updates:
                    self.last_update_id = max(self.last_update_id, update["update_id"]) + 1
                    if "callback_query" in update:
                        asyncio.create_task(self.handle_callback(update["callback_query"]))
                    elif "message" in update:
                        asyncio.create_task(self.handle_message(update["message"]))
            except Exception as e:
                logger.error(f"Erro no loop de long-polling: {e}")
                await asyncio.sleep(3)

    async def get_updates(self) -> list:
        url = f"{TELEGRAM_API_BASE}/getUpdates"
        params = {"offset": self.last_update_id, "timeout": 30}
        async with self.session.get(url, params=params, timeout=40) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("result", [])
            return []

    async def send_message(self, chat_id: int, text: str, reply_to_message_id: int | None = None, reply_markup: dict | None = None) -> dict | None:
        url = f"{TELEGRAM_API_BASE}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with self.session.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("result")
            logger.warning(f"Falha ao enviar mensagem: {await resp.text()}")
            return None

    async def edit_message(self, chat_id: int, message_id: int, text: str, reply_markup: dict | None = None):
        url = f"{TELEGRAM_API_BASE}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with self.session.post(url, json=payload) as resp:
                if resp.status != 200:
                    logger.debug(f"Aviso ao editar mensagem {message_id}: {await resp.text()}")
        except Exception as e:
            logger.debug(f"Exceção ao editar mensagem: {e}")

    async def answer_callback(self, callback_query_id: str, text: str = ""):
        url = f"{TELEGRAM_API_BASE}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        try:
            async with self.session.post(url, json=payload) as resp:
                pass
        except Exception:
            pass

    async def handle_callback(self, cb: dict):
        """Gerencia os fluxos interativos de perguntas quando o usuário clica em botões inline."""
        cb_id = cb["id"]
        chat_id = cb["message"]["chat"]["id"]
        message_id = cb["message"]["message_id"]
        data = cb.get("data", "")
        from_user = cb.get("from", {})
        user_id = str(from_user.get("id", ""))

        if TELEGRAM_ALLOWED_USER_ID and user_id != TELEGRAM_ALLOWED_USER_ID:
            await self.answer_callback(cb_id, "🔒 Acesso restrito.")
            return

        await self.answer_callback(cb_id)

        # 1. Início: Usuário clicou em 'Gerar Pesquisa no Antigravity'
        if data.startswith("pesq_init:"):
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
            await self.send_message(chat_id, texto_1, reply_markup={"inline_keyboard": botoes_1})

        # 2. Escolha de Foco -> Escolha de Formato
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
            await self.edit_message(chat_id, message_id, texto_2, reply_markup={"inline_keyboard": botoes_2})

        # 3. Escolha de Formato -> Dúvida Específica ou Finalizar
        elif data.startswith("pesq_p:"):
            _, prof_code, foco_code, slug = data.split(":", 3)
            dossie = obter_dossie_cache(slug) or {}
            tech_name = dossie.get("tech_name") or slug.replace("-", " ").title()
            foco_nome = FOCOS_MAP.get(foco_code, foco_code)
            prof_nome = FORMATOS_MAP.get(prof_code, prof_code)

            self.user_states[chat_id] = {
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
            await self.edit_message(chat_id, message_id, texto_3, reply_markup={"inline_keyboard": botoes_3})

        # 4. Conclusão Direta (Sem dúvida específica)
        elif data.startswith("pesq_done:"):
            _, _, prof_code, foco_code, slug = data.split(":", 4)
            self.user_states.pop(chat_id, None)
            pedido = criar_pedido_pesquisa(chat_id, slug, foco_code, prof_code, duvida_especifica="")
            await self.enviar_confirmacao_pedido(chat_id, pedido, message_id)

    async def enviar_confirmacao_pedido(self, chat_id: int, pedido: dict, message_id: int | None = None):
        """Envia a confirmação elegante e dispara a investigação automaticamente em background."""
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
            await self.edit_message(chat_id, message_id, msg_final)
        else:
            await self.send_message(chat_id, msg_final)

        # Dispara execução imediata em background no ambiente local
        asyncio.create_task(self.executar_pesquisa_background(chat_id, pedido))

    async def executar_pesquisa_background(self, chat_id: int, pedido: dict):
        """Executa a pesquisa e compilação de PDF no pool de threads e envia o resultado."""
        loop = asyncio.get_running_loop()
        try:
            logger.info(f"Disparando execução de pesquisa background para {pedido['tech_name']} ({pedido['id']})...")
            await loop.run_in_executor(executor, executar_pedido, pedido["id"])
            logger.info(f"Pesquisa concluída e PDF enviado com sucesso para chat {chat_id}.")
        except Exception as e:
            logger.error(f"Erro ao processar pesquisa background para {pedido['id']}: {e}", exc_info=True)
            await self.send_message(
                chat_id,
                f"❌ <b>Não foi possível compilar a pesquisa automaticamente.</b>\n<code>{str(e)[:250]}</code>\n\n"
                "<i>Você pode executá-la no terminal com:</i> <code>python scripts/executar_pesquisa.py --pedido " + pedido['id'] + "</code>"
            )

    async def handle_message(self, message: dict):
        chat_id = message["chat"]["id"]
        from_user = message.get("from", {})
        user_id = str(from_user.get("id", ""))
        text = message.get("text", "") or message.get("caption", "")

        # Validação de Usuário Autorizado
        if TELEGRAM_ALLOWED_USER_ID and user_id != TELEGRAM_ALLOWED_USER_ID:
            logger.warning(f"Acesso não autorizado bloqueado. User ID: {user_id}")
            await self.send_message(chat_id, "🔒 <i>Acesso restrito. Este é um bot pessoal e privado.</i>")
            return

        # 1. Checar se o usuário está respondendo a pergunta aberta do fluxo de pesquisa
        if chat_id in self.user_states and self.user_states[chat_id].get("stage") == "aguardando_duvida":
            state = self.user_states.pop(chat_id)
            duvida_texto = text.strip()
            pedido = criar_pedido_pesquisa(
                chat_id=chat_id,
                slug=state["slug"],
                foco_code=state["foco_code"],
                formato_code=state["prof_code"],
                duvida_especifica=duvida_texto
            )
            await self.enviar_confirmacao_pedido(chat_id, pedido)
            return

        # 2. Comandos básicos
        if text.startswith("/start") or text.startswith("/help"):
            msg_help = (
                "👋 <b>Bem-vindo ao Analisador de Reels & Tecnologias!</b>\n\n"
                "Para analisar uma dica de repositório ou tecnologia, basta <b>compartilhar ou colar o link do Reel do Instagram aqui</b>.\n\n"
                "🔍 <b>O que eu analiso:</b>\n"
                "• <b>Áudio:</b> O que o criador fala e explica (em Português).\n"
                "• <b>Vídeo:</b> Código na IDE, terminal e telas mostradas.\n"
                "• <b>Descrição:</b> A legenda completa e hashtags do post.\n"
                "• <b>GitHub:</b> Localizo o repositório oficial, estrelas, licença e guia de início rápido.\n\n"
                "🔬 <b>Pesquisas com o Antigravity:</b>\n"
                "Ao receber qualquer análise, você pode clicar em <b>'Gerar Pesquisa no Antigravity'</b> para disparar investigações técnicas profundas e gerar relatórios em PDF corporativo no seu repositório local."
            )
            await self.send_message(chat_id, msg_help)
            return

        # Checar se a mensagem contém link do Instagram
        instagram_url = extrair_url_instagram(text)
        if not instagram_url:
            # Mensagem comum sem link
            if text.startswith("/"):
                await self.send_message(chat_id, "Comando desconhecido. Envie um link do Instagram Reel para iniciar a análise.")
            return

        logger.info(f"Processando link do Instagram recebido: {instagram_url}")

        # Mensagem inicial de progresso
        status_msg = await self.send_message(
            chat_id,
            "📥 <b>[1/4] Baixando vídeo e metadados do Instagram...</b>\n<i>Aguarde alguns segundos.</i>",
            reply_to_message_id=message.get("message_id")
        )
        status_id = status_msg["message_id"] if status_msg else None

        loop = asyncio.get_running_loop()
        post: InstagramPost | None = None

        try:
            # 1. Download do Reel (executado em threadpool para não travar o loop)
            post = await loop.run_in_executor(executor, baixar_reel_instagram, instagram_url)

            if status_id:
                await self.edit_message(
                    chat_id,
                    status_id,
                    "🧠 <b>[2/4] Analisando áudio, vídeo e legenda com IA Multimodal...</b>\n<i>Inspecionando narração, tela de código e descrição.</i>"
                )

            # 2. Análise Multimodal com Gemini Flash
            analise = await loop.run_in_executor(executor, analisar_video_multimodal, post)

            qtd_techs = len(analise.technologies) if analise.technologies else 1
            if status_id:
                if analise.is_collection or qtd_techs > 1:
                    status_text = (
                        f"🔍 <b>[3/4] Toolkit identificado ({qtd_techs} ferramentas)!</b>\n"
                        f"<i>Auditando todos os {qtd_techs} repositórios no GitHub em paralelo...</i>"
                    )
                else:
                    tech_alvo = analise.technologies[0].tech_name if analise.technologies else analise.collection_title
                    status_text = (
                        f"🔍 <b>[3/4] Auditando '{tech_alvo}' no GitHub...</b>\n"
                        "<i>Obtendo métricas, estrelas e licença oficial.</i>"
                    )
                await self.edit_message(chat_id, status_id, status_text)

            # 3. Pesquisa e Validação no GitHub (Concorrente)
            dossie = await loop.run_in_executor(executor, enriquecer_e_validar_analise, analise, post.caption)

            # 4. Formatação e Envio do Dossiê Final
            texto_dossie, markup = formatar_dossie_telegram(dossie, instagram_url)

            if status_id:
                await self.edit_message(chat_id, status_id, texto_dossie, reply_markup=markup)
            else:
                await self.send_message(chat_id, texto_dossie, reply_markup=markup)

            logger.info(f"Análise finalizada com sucesso para {dossie.tech_name} ({len(dossie.items)} ferramentas)!")

        except Exception as e:
            logger.error(f"Erro ao processar Reel {instagram_url}: {e}", exc_info=True)
            err_str = str(e)
            if "503" in err_str or "UNAVAILABLE" in err_str or "temporarily unavailable" in err_str.lower():
                motivo_dica = (
                    "⚠️ <b>Instabilidade Temporária no Google Gemini (503 Service Unavailable).</b>\n\n"
                    "O download do vídeo foi feito com sucesso, mas os servidores da Google AI Studio apresentaram uma oscilação momentânea durante o processamento do vídeo.\n\n"
                    "<i>Dica: Reenvie o link novamente em alguns instantes.</i>"
                )
            elif "429" in err_str or "quota" in err_str.lower():
                motivo_dica = (
                    "⚠️ <b>Limite de Taxa ou Cota da API Excedido (429).</b>\n\n"
                    "Aguarde cerca de 1 minuto antes de enviar um novo vídeo."
                )
            elif "Private" in err_str or "Login" in err_str or "Instagram" in err_str:
                motivo_dica = (
                    "❌ <b>Falha ao baixar o Reel do Instagram.</b>\n\n"
                    f"<code>{err_str[:250]}</code>\n\n"
                    "<i>Dica: Verifique se o perfil não é privado ou se o vídeo ainda está disponível.</i>"
                )
            else:
                motivo_dica = (
                    "❌ <b>Não foi possível concluir a análise do vídeo.</b>\n\n"
                    f"<b>Motivo:</b> <code>{err_str[:300]}</code>\n\n"
                    "<i>Dica: Tente reenviar o link em instantes.</i>"
                )

            if status_id:
                await self.edit_message(chat_id, status_id, motivo_dica)
            else:
                await self.send_message(chat_id, motivo_dica)

        finally:
            if post:
                post.cleanup()


def main():
    ok, msg = validar_configuracoes(precisa_telegram=True)
    if not ok:
        print(f"❌ Erro de Configuração:\n{msg}")
        sys.exit(1)

    bot_service = TelegramBotService()
    try:
        asyncio.run(bot_service.start())
    except KeyboardInterrupt:
        print("\nBot encerrado pelo usuário.")


if __name__ == "__main__":
    main()
