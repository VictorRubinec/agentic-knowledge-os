---
name: pdf-generator
description: Motor central e linter para compilação de documentos MDX em PDFs de alta fidelidade visual (A4) com Playwright Chromium. Use sempre que o usuário solicitar geração, compilação, atualização ou validação de PDFs.
---

# Skill: Geração e Validação de PDFs (MDX -> PDF)

Esta skill orienta os agentes de IA a utilizarem o motor central unificado [`scripts/gerar_pdf.py`](file:///./scripts/gerar_pdf.py) para compilar e validar arquivos `.mdx` em PDFs A4 de alta fidelidade visual.

---

## 1. Regra Fundamental (Proibição de Scripts Paralelos)

- **REGRA DE OURO**: É estritamente **PROIBIDO criar novos scripts individuais** (seja em JS ou Python) para compilação de PDFs.
- Toda e qualquer geração de PDF a partir de `.mdx` DEVE utilizar o motor oficial:
  ```bash
  python scripts/gerar_pdf.py "<caminho_do_arquivo.mdx>"
  ```

---

## 2. Comandos Principais e Opções da CLI

| Ação Desejada | Comando |
| :--- | :--- |
| **Compilar um arquivo específico** | `python scripts/gerar_pdf.py "caminho/do/documento.mdx"` |
| **Definir arquivo de saída customizado** | `python scripts/gerar_pdf.py "documento.mdx" -o "pdf/saida.pdf"` |
| **Selecionar tema visual** | `python scripts/gerar_pdf.py "documento.mdx" -t corporate\|join4\|somos1\|rpg\|minimal` |
| **Apenas validar regras e linter (sem abrir Chromium)** | `python scripts/gerar_pdf.py "documento.mdx" --check-only` |
| **Compilar pasta inteira em lote** | `python scripts/gerar_pdf.py --dir "caminho/da/pasta"` |

---

## 3. Temas Visuais Suportados

- **`corporate`** (Padrão): Identidade visual sóbria em tons azul/ardósia (`#0284c7` / `#0f172a`), ideal para propostas comerciais, relatórios e planejamentos.
- **`join4`**: Identidade corporativa Empresa / Startup CSC / Cliente Corporativo em azul marinho profundo (`#0369a1` / `#1e293b`).
- **`somos1`**: Identidade Tríade / Somos 1 Tattoo Studio.
- **`rpg`**: Identidade visual para o Sistema Ordem 2 e Livros de Regras com tons rubros/escuros (`#dc2626` / `#18181b`).
- **`minimal`**: Layout limpo em escala de cinza para notas técnicas simplificadas.

---

## 4. Diretrizes de Qualidade MDX para Prevenção de Erros

Ao escrever ou editar documentos `.mdx` que serão convertidos para PDF, siga as seguintes regras:

1. **Diagramas Mermaid**:
   - **NUNCA use tags HTML de negrito (`<b>`, `<strong>`)** dentro de rótulos de nós do Mermaid. Use texto puro em maiúsculas ou quebras `<br/>`.
   - **Envolva rótulos em aspas duplas**: `A["Rótulo com (Parênteses)"] --> B["Segundo Passo"]`.
   - **Evite Árvores Horizontais Largas**: Nunca ramifique um nó raiz em 4 ou mais nós paralelos no modo `flowchart TD`. Use **fluxos sequenciais verticais (`flowchart TD`)** ou **tabelas Markdown**.
   - **Evite Subgrafos Empilhados Gigantes**: Nunca empilhe 3 ou mais subgrafos verticais em `flowchart LR`.
2. **Moedas e Valores Monetários**:
   - Sempre escreva `R$ 1.500,00` normalmente. O motor protege automaticamente contra colisões de LaTeX math e insere espaçamento não-separável.
3. **Componentes MDX**:
   - `<Timeline items={[...]} />` ou `<Timeline events={[...]} />`.
   - `<Callout title="..." type="info|warning|danger|success">...</Callout>`.
   - `<Badge label="..." type="trabalho|processo|projeto|ideia|danger" />`.
4. **Blocos de Código**:
   - Evite "dumps" de scripts operacionais longos (> 15 linhas com rotinas repetitivas).
   - Extraia apenas **Snippets Cirúrgicos (< 10 linhas)** focados na regra de negócio e use **Tabelas de Passos de Execução**.

---

## 5. Auditoria e Diagnóstico de Erros

O motor `gerar_pdf.py` conta com 4 camadas de verificação automática:
1. **Linter Pré-Renderização**: Analisa frontmatter, tags HTML em Mermaid, sintaxe de componentes e colisões de moedas.
2. **Listener de Erros no Chromium**: Detecta `pageerror` e `console.error` de JavaScript antes do print.
3. **Auditoria do DOM**: Garante que o container `#content` não ficou vazio.
4. **Pós-Verificação Binária via `pypdf`**: Abre o PDF gerado e valida se o número de páginas, palavras e caracteres extraídos correspondem ao conteúdo esperado, bloqueando PDFs corrompidos ou com apenas capa.
