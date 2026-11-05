#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/downloader.py — Download de Mídia e Metadados do Instagram
"""

import re
import uuid
import logging
from pathlib import Path
from dataclasses import dataclass, field
import yt_dlp

from config import TEMP_MEDIA_DIR

logger = logging.getLogger("media_downloader")

# Expressões regulares para detecção de links do Instagram e YouTube Shorts
INSTAGRAM_URL_REGEX = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:reel|p|reels)/([A-Za-z0-9_-]+)',
    re.IGNORECASE
)

YOUTUBE_URL_REGEX = re.compile(
    r'https?://(?:www\.|m\.)?(?:youtube\.com/shorts/|youtu\.be/)([A-Za-z0-9_-]+)',
    re.IGNORECASE
)


@dataclass
class InstagramPost:
    """Estrutura com os dados extraídos de uma postagem do Instagram ou YouTube."""
    id: str
    url: str
    video_path: Path
    caption: str = ""
    author: str = ""
    hashtags: list[str] = field(default_factory=list)

    def cleanup(self):
        """Remove o arquivo de vídeo temporário do disco após processamento."""
        if self.video_path and self.video_path.exists():
            try:
                self.video_path.unlink()
                logger.info(f"Arquivo temporário removido: {self.video_path.name}")
            except Exception as e:
                logger.warning(f"Falha ao remover arquivo temporário {self.video_path}: {e}")


# Alias para clareza
MediaPost = InstagramPost


def extrair_url_midia(texto: str) -> str | None:
    """Encontra e extrai a primeira URL válida do Instagram ou YouTube Shorts em um texto."""
    ig_match = INSTAGRAM_URL_REGEX.search(texto)
    if ig_match:
        shortcode = ig_match.group(1)
        return f"https://www.instagram.com/reel/{shortcode}/"
    yt_match = YOUTUBE_URL_REGEX.search(texto)
    if yt_match:
        shortcode = yt_match.group(1)
        return f"https://www.youtube.com/shorts/{shortcode}"
    return None


def extrair_url_instagram(texto: str) -> str | None:
    """Encontra e extrai a primeira URL válida do Instagram presente em um texto."""
    match = INSTAGRAM_URL_REGEX.search(texto)
    if match:
        shortcode = match.group(1)
        return f"https://www.instagram.com/reel/{shortcode}/"
    return None


def baixar_reel_instagram(url: str, cookies_path: Path | None = None) -> InstagramPost:
    """
    Realiza o download do vídeo MP4 e extrai a legenda completa e metadados do post (Instagram ou YouTube).
    
    Args:
        url: URL do Reel/Post do Instagram ou YouTube Shorts.
        cookies_path: Caminho opcional para arquivo de cookies.
        
    Returns:
        InstagramPost contendo o caminho do vídeo local e a legenda textual.
        
    Raises:
        RuntimeError: Se o download falhar ou a mídia não estiver disponível.
    """
    clean_url = extrair_url_midia(url) or url
    unique_id = str(uuid.uuid4())[:8]
    output_template = str(TEMP_MEDIA_DIR / f"media_{unique_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": False,
    }

    if cookies_path and cookies_path.exists():
        ydl_opts["cookiefile"] = str(cookies_path)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            if not info:
                raise RuntimeError("yt-dlp não conseguiu extrair informações da URL informada.")

            # Identificar o arquivo baixado
            post_id = info.get("id") or unique_id
            caption = info.get("description") or info.get("title") or ""
            author = info.get("uploader") or info.get("channel") or ""

            # Extração de hashtags da legenda
            hashtags = re.findall(r'#(\w+)', caption)

            # Localizar o arquivo .mp4 salvo
            expected_file = Path(ydl.prepare_filename(info))
            if not expected_file.exists():
                # Tentar encontrar com o prefixo
                candidatos = list(TEMP_MEDIA_DIR.glob(f"media_{unique_id}*")) + list(TEMP_MEDIA_DIR.glob(f"reel_{unique_id}*"))
                if candidatos:
                    expected_file = candidatos[0]
                else:
                    raise FileNotFoundError(f"Arquivo de vídeo não foi gravado no disco: {output_template}")

            return InstagramPost(
                id=post_id,
                url=clean_url,
                video_path=expected_file,
                caption=caption.strip(),
                author=author.strip(),
                hashtags=hashtags
            )

    except Exception as e:
        logger.error(f"Erro ao baixar vídeo ({url}): {e}")
        raise RuntimeError(f"Falha ao extrair vídeo de {clean_url}: {e}") from e


baixar_midia = baixar_reel_instagram
