# Dockerfile para Shard Cloud (shardcloud.app)
# Executa a API de automação, validação e compilação de PDFs do Second Brain

FROM python:3.11-slim

# Evita prompts interativos e define encoding
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Instala dependências do sistema e Node.js para ferramentas de CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala Playwright e navegadores headless com permissão global
RUN mkdir -p /ms-playwright && playwright install chromium --with-deps && chmod -R 777 /ms-playwright

# Instala ferramentas globais de CLI
RUN npm install -g @playwright/cli@latest

# Cria usuário não-root para conformidade DevSecOps (Aikido IaC Scan)
RUN useradd -m -u 1000 appuser

# Copia código da aplicação e define permissões
COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "scripts.server:app", "--host", "0.0.0.0", "--port", "8000"]
