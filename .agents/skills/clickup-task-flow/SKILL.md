---
name: clickup-task-flow
description: Orquestração completa do ciclo de vida de tarefas da Empresa / Startup/Produto integradas ao ClickUp. Use sempre que o usuário mencionar uma tarefa do ClickUp (por ID ou link), solicitar criação/atualização de dossiê de tarefa, compilação de PDF da tarefa, ou sincronização/anexo de relatórios no ClickUp.
---

# Skill: Orquestração de Tarefas ClickUp (Empresa / Startup Produto)

Esta skill guia o agente no cumprimento estrito das **Diretrizes 16 e 17 do AGENTS.md**: gestão de escopo imutável, rastreabilidade contínua de tarefas de Produto, compilação de relatórios em PDF de alta fidelidade e anexação controlada no ClickUp com gate de aprovação humana.

---

## 1. Princípios Inegociáveis

1. **Rastreabilidade de Ponta a Ponta**: Toda tarefa deve ser registrada em `trabalho/join4/produto/tarefas/task-XXX-slug.mdx` utilizando o template mestre [`00-meta/TEMPLATE_TAREFA.mdx`](file:///./00-meta/TEMPLATE_TAREFA.mdx).
2. **Escopo Imutável & Aditivos**: O escopo original extraído do ClickUp **nunca deve ser deletado ou alterado**. Novos requisitos surgidos no decorrer da execução devem ser adicionados na seção `### Aditivos de Escopo`.
3. **Gate Mandatório de Aprovação Humana**: **NUNCA** anexe arquivos ou poste relatórios finais no ClickUp sem exibir o link do PDF compilado ao usuário e aguardar seu "de acordo" explícito.
4. **Motor Central Unificado de PDF**: Sempre utilize `python scripts/gerar_pdf.py` para gerar e auditar o layout do PDF.

---

## 2. Fluxo Operacional (Passo a Passo)

### Passo 1: Captura e Sincronização Inicial
Ao receber o ID da tarefa (ex: `868fd1234`) ou quando solicitado a sincronizar:
```bash
python scripts/analisador_clickup.py --task <TASK_ID>
```
*Este comando:*
- Consulta a API do ClickUp.
- Gera a análise de módulo, impacto arquitetural e checkpoints.
- Cria ou localiza o arquivo `trabalho/join4/produto/tarefas/task-XXX-<slug>.mdx`.
- Atualiza o painel central [`trabalho/join4/produto/tarefas/README.mdx`](file:///./trabalho/join4/produto/tarefas/README.mdx).

### Passo 2: Execução Técnica e Registro Contínuo
Conforme a demanda técnica avança:
- Documente comandos executados e arquivos modificados na tabela `## Registro de Execução & Comandos`.
- Atualize os itens do checklist `<ClickUpChecklist />` marcando `done={true}` para o que foi concluído.
- Adicione uma nova entrada na `<Timeline />` ao mudar de fase ou concluir uma etapa crítica.

### Passo 3: Validação de Layout e Pré-visualização do PDF
Antes de gerar o arquivo final, rode o linter para garantir que não há quebras órfãs ou diagramas distorcidos:
```bash
python scripts/gerar_pdf.py "trabalho/join4/produto/tarefas/task-XXX-<slug>.mdx" --check-only
```

### Passo 4: Compilação Oficial do PDF
Gere o PDF com a identidade corporativa da Empresa / Startup:
```bash
python scripts/gerar_pdf.py "trabalho/join4/produto/tarefas/task-XXX-<slug>.mdx" -t join4
```
O PDF será compilado na pasta `pdf/` do respectivo módulo ou diretório.

### Passo 5: Gate de Aprovação Humana (PAUSA OBRIGATÓRIA)
Apresente o link do PDF gerado no chat com uma mensagem formal:
> "O dossiê da tarefa **[Nome da Tarefa]** foi compilado com sucesso:
> 📄 [task-XXX-slug.pdf](file:///./trabalho/join4/produto/tarefas/pdf/task-XXX-slug.pdf)
> 
> Você aprova o anexo deste PDF e a atualização do status na tarefa `<TASK_ID>` do ClickUp?"

**Aguarde a resposta do usuário antes de prosseguir para o Passo 6.**

### Passo 6: Anexo e Atualização no ClickUp (Pós-Aprovação)
Somente após o usuário autorizar explicitamente, envie o PDF para o ClickUp:
```bash
python scripts/analisador_clickup.py --task <TASK_ID> --attach-pdf "caminho/do/arquivo.pdf"
```
Se for o fechamento ou parecer técnico:
```bash
python scripts/analisador_clickup.py --task <TASK_ID> --post-comment
```

---

## 3. Comandos Rápidos de Referência

| Ação | Comando |
| :--- | :--- |
| **Sincronizar tarefa do ClickUp** | `python scripts/analisador_clickup.py --task <ID>` |
| **Validar regras de PDF sem compilar** | `python scripts/gerar_pdf.py "<task.mdx>" --check-only` |
| **Compilar PDF oficial (Tema Empresa / Startup)** | `python scripts/gerar_pdf.py "<task.mdx>" -t join4` |
| **Anexar PDF no ClickUp (Após aprovação)** | `python scripts/analisador_clickup.py --task <ID> --attach-pdf "<arquivo.pdf>"` |
| **Postar parecer técnico no ClickUp** | `python scripts/analisador_clickup.py --task <ID> --post-comment` |
