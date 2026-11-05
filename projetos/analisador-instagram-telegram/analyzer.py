#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/analyzer.py — Análise Multimodal de Áudio, Vídeo e Legenda com Gemini Flash
"""

import time
import json
import logging
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from downloader import InstagramPost

logger = logging.getLogger("video_analyzer")


class IdentifiedTechnologyItem(BaseModel):
    """Schema estruturado de uma tecnologia individual identificada no vídeo."""
    tech_name: str = Field(description="Nome da biblioteca, ferramenta, framework ou repositório individual.")
    github_candidate: str = Field(default="", description="Possível repositório no GitHub (ex: 'jaytel0/taste', 'kaomei/stickman-video-director' ou apenas o slug do repo).")
    official_url_candidate: str = Field(default="", description="URL oficial ou documentação exibida no vídeo, falada ou na legenda.")
    summary: str = Field(description="Resumo claro e conciso de 1 a 2 frases em Português do Brasil explicando o que a tecnologia é e qual problema resolve.")
    audio_highlights: str = Field(default="", description="Destaques do que o criador de conteúdo falou na narração sobre esta ferramenta específica (em português).")
    video_highlights: str = Field(default="", description="Destaques visuais dos frames do vídeo onde esta ferramenta aparece (código, telas de terminal, IDE, browser, UI em português).")
    install_commands: str = Field(default="", description="Comandos de instalação, terminal ou execução identificados para esta ferramenta (ex: 'npx taste init', 'pip install ...').")
    key_tags: list[str] = Field(default_factory=list, description="Tags técnicas relevantes (ex: ['Next.js', 'Tailwind', 'Playwright', 'Design']).")


class MultimodalReelAnalysis(BaseModel):
    """Schema estruturado da análise multimodal do Reel (suporta ferramenta única ou coleção/toolkit)."""
    is_collection: bool = Field(description="True se o vídeo apresenta múltiplas ferramentas (ex: 'Top 5 ferramentas', 'Toolkit de Web Design', compilação de repositórios), False se foca exclusivamente em 1 ferramenta.")
    collection_title: str = Field(default="", description="Título unificado da coleção ou tema apresentado (ex: 'Claude Web Design Toolkit', 'Top 5 Repos de IA'). Se for apenas 1 ferramenta, pode ser o próprio nome dela.")
    collection_overview: str = Field(default="", description="Visão geral e contextual em Português do Brasil explicando como essas ferramentas se conectam ou a proposta geral do vídeo.")
    technologies: list[IdentifiedTechnologyItem] = Field(description="Lista de todas as ferramentas identificadas no vídeo. Se o vídeo mostrar 3, 5 ou mais ferramentas, liste todas elas individualmente nesta lista.")


# Alias retrocompatível caso algum módulo antigo importe MultimodalAnalysisResult
MultimodalAnalysisResult = MultimodalReelAnalysis


def analisar_video_multimodal(post: InstagramPost) -> MultimodalReelAnalysis:
    """
    Envia o vídeo MP4 e a legenda para a Gemini File API e executa a percepção tripla sincronizada.
    Identifica se o vídeo trata de uma única tecnologia ou de um toolkit/compilação com múltiplas ferramentas.
    
    Args:
        post: Objeto InstagramPost contendo o caminho do vídeo local e a legenda.
        
    Returns:
        MultimodalReelAnalysis com a lista de entidades e insights extraídos.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não foi configurada. Defina no .env ou nas variáveis de ambiente.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    logger.info(f"Fazendo upload do vídeo ({post.video_path.name}) para a Gemini File API...")
    uploaded_file = client.files.upload(file=str(post.video_path))
    logger.info(f"Upload concluído. File URI: {uploaded_file.uri}. Aguardando ativação...")

    try:
        # Aguarda o processamento do vídeo no Google Cloud com polling resiliente
        max_attempts = 20
        attempt = 0
        consecutive_errors = 0
        while uploaded_file.state.name == "PROCESSING" and attempt < max_attempts:
            time.sleep(3)
            attempt += 1
            try:
                uploaded_file = client.files.get(name=uploaded_file.name)
                consecutive_errors = 0
            except Exception as err:
                consecutive_errors += 1
                logger.warning(
                    f"Oscilação transitória na Gemini API ao consultar status do vídeo ({err}). "
                    f"Tentativa {consecutive_errors}/5 de recuperação..."
                )
                if consecutive_errors >= 5:
                    raise
                time.sleep(2)

        if uploaded_file.state.name != "ACTIVE":
            raise RuntimeError(f"O arquivo de vídeo não ficou ativo para inferência. Estado atual: {uploaded_file.state.name}")

        logger.info("Vídeo ativo. Executando análise multimodal tripla (1:N)...")

        system_instruction = (
            "Você é um Engenheiro de Software Sênior e Especialista em Engenharia Reversa de Conteúdo Técnico. "
            "Sua missão é inspecionar minuciosamente este vídeo de Reel do Instagram (analisando a fala em áudio, "
            "os frames visuais em tela com código/terminal/navegador e a legenda textual fornecida).\n\n"
            "DETECÇÃO MANDATÓRIA DE COMPILAÇÕES E TOOLKITS (1:N):\n"
            "- Se o vídeo apresentar mais de uma tecnologia, biblioteca ou repositório (ex: 'Top 5 ferramentas', 'Toolkit de Web Design', '3 repositórios que você precisa conhecer'), "
            "você DEVE marcar `is_collection=True` e extrair CADA UMA das ferramentas individualmente na lista `technologies`.\n"
            "- NUNCA condense ou descarte ferramentas secundárias se o criador apresentou uma lista (ex: 5 ferramentas para web design). Extraia todas as 5 individualmente!\n"
            "- Se o vídeo focar exclusivamente em apenas 1 tecnologia do início ao fim, marque `is_collection=False` e preencha a lista `technologies` com exatamente 1 item.\n\n"
            "REGRA MANDATÓRIA DE IDIOMA:\n"
            "Todos os resumos, visões gerais, análises de áudio e análises de vídeo DEVEM ser estritamente redigidos em Português do Brasil (pt-BR), "
            "de forma fluente, técnica e profissional. Mesmo que o vídeo original seja em inglês, traduza e explique tudo em português."
        )

        prompt_conteudo = f"""
Analise detalhadamente este vídeo do Instagram e extraia as informações técnicas:

--- METADADOS DA POSTAGEM ---
Autor: {post.author or 'Não informado'}
URL Original: {post.url}
Legenda / Descrição do Post:
\"\"\"{post.caption}\"\"\"
Hashtags: {', '.join(post.hashtags) if post.hashtags else 'Nenhuma'}
-----------------------------

INSTRUÇÕES OBRIGATÓRIAS:
1. DETECÇÃO DE COMPILAÇÃO / TOOLKIT: Observe se o vídeo lista múltiplas ferramentas em sequência (ex: ferramenta 1, ferramenta 2, ferramenta 3...). Se sim, crie uma entrada separada para cada uma no array 'technologies' com seus respectivos nomes, comandos, repositórios e descrições.
2. IDIOMA: Escreva OBRIGATORIAMENTE em Português do Brasil (pt-BR) todos os campos de texto ('collection_overview', 'summary', 'audio_highlights', 'video_highlights'). Se o conteúdo original for em inglês, traduza e sintetize em português.
3. ÁUDIO: Ouça atentamente a voz/fala do criador para cada ferramenta mencionada.
4. VÍDEO / VISÃO: Inspecione cada frame de tela (IDE, VS Code, terminal de comandos, barra de navegação de browser, títulos em overlay). Identifique repositórios, comandos CLI e URLs para cada ferramenta.
5. RIGOR DE OCR EM NOMES DE REPOSITÓRIOS: Ao ler URLs e perfis do GitHub na tela, inspecione pixel a pixel a grafia exata de cada letra (cuidado com confusões comuns de OCR: 'a' vs 'e', 'o' vs '0', 'l' vs '1', 'rn' vs 'm'). Forneça preferencialmente no formato limpo 'owner/repo' ou nome do repositório em 'github_candidate'.
"""

        def _chamar_com_retry(nome_modelo: str, max_tentativas: int = 3):
            for i in range(max_tentativas):
                try:
                    return client.models.generate_content(
                        model=nome_modelo,
                        contents=[uploaded_file, prompt_conteudo],
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=MultimodalReelAnalysis,
                            temperature=0.2,
                        ),
                    )
                except Exception as api_err:
                    if i < max_tentativas - 1:
                        espera = 2 * (i + 1)
                        logger.warning(
                            f"Modelo {nome_modelo} retornou oscilação ({api_err}). "
                            f"Aguardando {espera}s antes da nova tentativa..."
                        )
                        time.sleep(espera)
                    else:
                        raise

        # Modelos homologados com suporte multimodal ativos na API (com rotação automática de fallback)
        modelos_candidatos = [
            "gemini-3-flash-preview",
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
        ]

        response = None
        ultimo_erro = None

        for modelo in modelos_candidatos:
            try:
                logger.info(f"Submetendo análise multimodal para o modelo: {modelo}...")
                response = _chamar_com_retry(modelo, max_tentativas=2)
                if response and response.text:
                    logger.info(f"Modelo {modelo} concluiu a análise com sucesso.")
                    break
            except Exception as e:
                ultimo_erro = e
                logger.warning(f"Modelo {modelo} indisponível ou em alta demanda ({e}). Testando próximo modelo da lista...")

        if not response or not response.text:
            raise RuntimeError(f"Nenhum modelo Gemini conseguiu processar o vídeo no momento. Último erro: {ultimo_erro}")

        raw_json = response.text
        logger.info("Análise concluída com sucesso pela IA.")
        data = json.loads(raw_json)
        return MultimodalReelAnalysis(**data)

    finally:
        # Limpeza na nuvem (Good Citizen Pattern)
        try:
            client.files.delete(name=uploaded_file.name)
            logger.info("Arquivo temporário removido da Gemini File API com sucesso.")
        except Exception as e:
            logger.warning(f"Aviso ao remover arquivo remoto da Gemini API: {e}")
