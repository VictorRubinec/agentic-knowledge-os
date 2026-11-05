# 📱 Analisador Multimodal de Reels do Instagram & Telegram Bot

> **Pipeline autônomo acionado sob demanda**: ao receber um link de Reel ou Post do Instagram pelo Telegram, o bot faz o download da mídia, aciona inteligência artificial multimodal (Gemini 2.5 Flash) para analisar simultaneamente o **áudio falado**, os **frames de vídeo** (telas de código/terminal/browser) e o **texto da legenda**, auditando e localizando o repositório oficial no GitHub com métricas reais.

---

## 🏗️ Arquitetura do Sistema

```
[Usuário envia link do Reel no Telegram]
                  │
                  ▼
         [Telegram Bot API]
                  │
                  ▼
       [1. Download via yt-dlp]
         ├── Vídeo MP4 (com faixa de áudio)
         └── Metadados JSON (legenda e hashtags)
                  │
                  ▼
   [2. IA Multimodal (Gemini 2.5 Flash)]
         ├── Áudio: Transcrição da fala e motivação
         ├── Vídeo: OCR de IDE, terminal, browser e UI
         └── Legenda: Contexto textual do post
                  │
                  ▼
   [3. Auditoria & Pesquisa no GitHub]
         ├── Localização do repositório oficial
         ├── Métricas (Stars, Forks, Licença, Commits)
         └── Guia de início rápido e veredito
                  │
                  ▼
[Entrega do Dossiê Formatado no Telegram com Botões Inline]
```

---

## 🚀 Como Configurar e Executar

### 1. Pré-Requisitos

- Python 3.11+
- Chave de API do **Google Gemini** (gratuita em [Google AI Studio](https://aistudio.google.com/))
- Token de Bot do **Telegram** (obtido gratuitamente com o [@BotFather](https://t.me/botfather))

### 2. Instalação de Dependências

```bash
cd projetos/analisador-instagram-telegram
pip install -r requirements.txt
```

### 3. Configuração de Variáveis (`.env`)

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Preencha as chaves:

```env
TELEGRAM_BOT_TOKEN="seu_token_aqui"
TELEGRAM_ALLOWED_USER_ID="seu_user_id"
GEMINI_API_KEY="sua_gemini_api_key"

# Opcional (para aumentar o rate limit de 60 para 5.000 req/hora na GitHub API):
GITHUB_TOKEN="ghp_seu_token"
```

> **Nota de Conveniência:** O sistema também lê automaticamente as configurações de `scripts/telegram_config.json` caso já estejam preenchidas no seu ambiente.

---

## 🛠️ Modos de Uso

### Modo 1: Teste Direto via Linha de Comando (CLI)

Você pode testar qualquer link de Reel sem precisar iniciar o bot do Telegram:

```bash
python cli.py "https://www.instagram.com/reel/C-xyz123/"
```

### Modo 2: Executar o Bot no Telegram

Inicie o serviço de escuta contínua:

```bash
python bot.py
```

Agora basta abrir o seu chat no Telegram com o bot e enviar qualquer link do Instagram!

---

## 📋 Exemplo de Dossiê Retornado

```html
🔍 TECNOLOGIA IDENTIFICADA: FastHTML 📦 Repositório: AnswerDotAI/fasthtml ⭐
Métricas: 8.4k stars | 620 forks | Python 📜 Licença: Apache-2.0 | 🕒
Atualizado: Há 2 dias 💡 O QUE É E O QUE RESOLVE: Framework moderno que permite
criar SPAs completas e reativas usando 100% Python puro, integrando HTMX
nativamente sob o capô sem necessidade de JavaScript ou React. 📺 DESTAQUES DA
PERCEPÇÃO TRIPLA: • Áudio: O criador explica que substituiu o Streamlit por ter
controle total de CSS e layout. • Vídeo/Tela: Mostrou a tela da IDE criando um
componente reativo em apenas 5 linhas de código. ⚙️ GUIA DE INÍCIO RÁPIDO: pip
install python-fasthtml ⚖️ VEREDITO TÉCNICO: Projeto de alta maturidade (8.4k
stars). Comunidade ativa e adoção ampla. Manutenção muito frequente com commits
recentes.
```

---

## 🛡️ Segurança e Resiliência

- **Filtro Anti-Abuso:** O bot só responde ao seu `TELEGRAM_ALLOWED_USER_ID`, ignorando mensagens de terceiros.
- **Good Citizen Pattern:** Todos os arquivos de vídeo baixados no disco local e os arquivos enviados para a Gemini File API são **automaticamente excluídos** após a conclusão da análise, evitando consumo desnecessário de disco ou nuvem.
