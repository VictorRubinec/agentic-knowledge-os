---
name: second-brain-doctor
description: Auditoria contínua de integridade, saúde de links, conformidade de frontmatter e regeneração do catálogo mestre (ORGANIZATION.md) do Second Brain. Use sempre que criar, mover ou renomear arquivos MDX, ou quando solicitado a verificar a saúde e integridade do repositório.
---

# Skill: Second Brain Doctor (Saúde & Integridade de Conhecimento)

Esta skill audita, valida e garante a consistência do repositório de anotações e documentos executivos, assegurando que não existam links quebrados, frontmatters inválidos ou índices desatualizados.

---

## 1. Quando Utilizar Esta Skill

- Sempre após criar, renomear, mover ou excluir arquivos `.mdx` ou `.md`.
- Antes de consolidar entregas ou gerar relatórios de auditoria.
- Quando o usuário perguntar sobre a saúde do repositório ("verifique a integridade", "audite os links", "atualize o índice").
- Antes de rodar deploys ou commits em lote.

---

## 2. Protocolo de Diagnóstico e Correção (Passo a Passo)

### Passo 1: Validação de Metadados e Frontmatter
Verifica se todos os arquivos `.mdx` contêm os campos obrigatórios (`title`, `category`, `tags`, `updatedAt`, `status`) e as seções `Linha do Tempo` e `Assuntos Relacionados`:
```bash
python scripts/validar_frontmatter.py
```
*Se houver falha:* Identifique o arquivo relatado e adicione os campos ou seções ausentes conforme o [`00-meta/TEMPLATE_NOTA.mdx`](file:///./00-meta/TEMPLATE_NOTA.mdx).

### Passo 2: Auditoria de Links e Hiperlinks Cruzados
Rastreia links quebrados, caminhos relativos inexistentes ou links absolutos locais proibidos:
```bash
python scripts/validar_links.py
```
*Se houver falha:* Corrija o destino do link para o caminho relativo correto ou atualize para o slug atualizado do documento.

### Passo 3: Sincronização do Catálogo Mestre (ORGANIZATION.md)
Regenera a matriz de categorias e o índice de navegação dinâmico mantendo intacto o conteúdo manual:
```bash
python scripts/gerar_organization.py --write
```
*Dica:* Para apenas validar se o índice está atualizado sem alterar o arquivo, use `python scripts/gerar_organization.py --check`.

### Passo 4: Execução da Suíte de Testes
Executa a validação formal com o `pytest`:
```bash
pytest tests/test_validators.py
```

---

## 3. Formato do Relatório de Diagnóstico

Ao concluir a execução do diagnóstico, retorne ao usuário um resumo executivo com a seguinte estrutura:

```markdown
### 🩺 Relatório de Saúde do Second Brain
- **Frontmatter e Metadados:** ✅ 100% em conformidade (ou ❌ N pendências)
- **Links & Referências:** ✅ 0 links quebrados (ou ❌ N violações encontradas)
- **Catálogo Mestre (ORGANIZATION.md):** ✅ Sincronizado com os arquivos em disco
- **Suíte de Testes (pytest):** ✅ Passou em N testes
```
