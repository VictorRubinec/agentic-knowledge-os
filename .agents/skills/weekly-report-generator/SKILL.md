---
name: weekly-report-generator
description: Consolidação e geração automática do Status Report Semanal Executivo de Produto e Engenharia da Empresa / Startup em MDX e PDF corporativo A4. Use sempre que o usuário pedir para gerar o relatório semanal, consolidar o status da sprint, fechar o relatório de tarefas ou gerar PDF para a diretoria.
---

# Skill: Gerador de Status Report Semanal Executivo (Empresa / Startup Produto)

Esta skill orquestra a varredura das tarefas ativas da área de Produto da Empresa / Startup em `trabalho/join4/produto/tarefas/`, sintetizando a evolução da sprint, métricas de entrega, matriz MoSCoW e gerando o documento executivo em MDX com compilação direta para PDF corporativo A4.

---

## 1. Quando Utilizar Esta Skill

- Toda sexta-feira ou fechamento de ciclo/sprint.
- Quando o usuário solicitar: *"gere o status report da semana"*, *"compile o relatório semanal"*, *"feche a sprint no relatório executivo"*.
- Para gerar apresentações executivas consolidadas para diretoria, clientes ou investidores.

---

## 2. Fluxo de Execução

### Passo 1: Execução do Motor de Agregação
Execute o script agregador:
```bash
python scripts/gerar_status_report_semanal.py
```

Opções disponíveis:
| Flag | Descrição |
| :--- | :--- |
| `--theme <tema>` | Tema visual do PDF (`join4`, `corporate`, `minimal`). Padrão: `join4`. |
| `--dias <N>` | Janela temporal em dias para incluir tarefas (padrão: 14 dias). |
| `--no-pdf` | Gera somente o documento MDX sem acionar o Playwright. |

### Passo 2: Verificação do Documento e PDF Gerados
O motor gera automaticamente:
1. **Documento MDX**: `trabalho/join4/produto/relatorios/status-report-semana-XX-YYYY.mdx`
2. **PDF A4 Corporativo**: `trabalho/join4/produto/relatorios/pdf/status-report-semana-XX-YYYY.pdf`

### Passo 3: Apresentação ao Usuário
Apresente o resumo das métricas e o link direto para o PDF compilado:
```markdown
### 📊 Status Report Semanal — Semana XX/YYYY Concluído
- **Total de Iniciativas:** N demandas
- **Índice de Conclusão:** X% concluído
- **Dossiê MDX:** [status-report-semana-XX-YYYY.mdx](trabalho/join4/produto/relatorios/status-report-semana-XX-YYYY.mdx)
- **PDF Executivo A4:** 📄 [status-report-semana-XX-YYYY.pdf](trabalho/join4/produto/relatorios/pdf/status-report-semana-XX-YYYY.pdf)
```

### Passo 4: Atualização de Navegação e Memória
Sempre execute o sincronizador de catálogo e registre a emissão do relatório em `MEMORY.md`:
```bash
python scripts/gerar_organization.py --write
```
