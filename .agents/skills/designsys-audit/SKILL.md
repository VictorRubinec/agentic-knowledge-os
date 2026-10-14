---
name: designsys-audit
description: >-
  Executa a extração, auditoria de CSS e mapeamento de Design System de sites ao vivo
  utilizando a ferramenta designsys. Organiza os tokens W3C, variáveis CSS, conformidade
  WCAG 2.2 AA e gera relatórios em trabalho/sites/relatorios/<slug>/.
---

# Extração e Auditoria de Design System com `designsys`

Esta skill orienta o agente na execução de análises de CSS, tokens de design e auditoria de interfaces web a partir de URLs fornecidas pelo usuário.

---

## Quando Utilizar

- Quando o usuário pedir:
  - "analise o css do site X"
  - "extraia o design system de Y"
  - "audite as cores e tipografia de Z"
  - "faça um relatório de design tokens de tal site"

---

## Procedimento de Execução

### 1. Executar o Script Orquestrador

Rode o script `scripts/analisar_css_site.py` a partir da raiz do repositório garantindo que Python rode em modo UTF-8 (`-X utf8`):

```bash
python -X utf8 scripts/analisar_css_site.py "https://exemplo.com" --pages 3
```

#### Parâmetros Úteis:

- `--pages <N>`: Número de páginas internas a mapear (padrão: 3).
- `--login`: Se o site estiver atrás de autenticação / login corporativo.
- `--no-dark`: Se não precisar mapear tema escuro (acelera a execução).
- `--no-viewports`: Se não precisar inspecionar viewports mobile/tablet.
- `--headed`: Se precisar abrir o navegador visível (ex: CAPTCHAs manuais).

---

## Destino e Estrutura dos Arquivos

O script automaticamente gerará ou atualizará a estrutura:

```text
trabalho/sites/relatorios/<slug>/
├── relatorio-<slug>.mdx         # Documento mestre MDX (Linha do Tempo, tokens, diagnóstico WCAG)
└── extracao/                    # Entregáveis brutos
    ├── design-system.pdf        # PDF diagramado pronto para circular
    ├── DESIGN-SYSTEM.md         # Regras acionáveis para agentes de IA
    ├── tokens.json              # Design tokens no padrão W3C DTCG
    ├── variables.css            # Variáveis CSS com escopos dark e clamp()
    ├── tailwind.config.js       # Bloco theme.extend
    ├── style-guide.html         # Guia visual interativo navegável
    ├── components.json          # Estilos computados com :hover, :focus, :active
    ├── audit.md                 # Relatório detalhado da auditoria
    ├── screenshots/             # Capturas de tela das páginas analisadas
    └── assets/                  # Ícones, fontes e logos extraídos
```

---

## Diretrizes de Preservação e Linha do Tempo

1. **Nunca Duplicar Arquivos**: Se o site já tiver sido analisado anteriormente, o script adicionará uma nova entrada na seção `## 📜 Linha do Tempo` do `relatorio-<slug>.mdx` existente, preservando o histórico.
2. **Atualização da Memória**: Após concluir qualquer análise, atualize o arquivo `MEMORY.md` com a data e resumo do site auditado.
