---
name: anti-rationalization
description: Tabelas anti-racionalização e portões de disciplina de engenharia para agentes de IA (Addy Osmani). Impede que agentes tomem atalhos, ignorem diretrizes do AGENTS.md, pulem linters de PDF ou entreguem tarefas sem validação.
---

# Skill: Anti-Rationalization & Disciplina de Engenharia (Addy Osmani)

Esta skill codifica o padrão de **Anti-Rationalization Tables** (desenvolvido por Addy Osmani em `addyosmani/agent-skills`), adaptado especificamente para a operação rigorosa do repositório de anotações e desenvolvimento de projetos com agentes de IA (Antigravity e Claude).

---

## 1. Princípio Fundamental

Agentes de IA frequentemente racionalizam desculpas para economizar esforço ou evitar atritos operacionais (ex: pular compilação de PDFs, não atualizar o `ORGANIZATION.md`, inventar código sem testes). 

**Regra de Ouro**: A racionalização é uma falha de engenharia. Toda ação com efeitos colaterais no repositório deve passar por portões determinísticos de verificação.

---

## 2. Tabela Mestre Anti-Racionalização do Repositório

| Racionalização da IA (Desculpa Comum) | Realidade & Risco Técnico | Regra Estrita Mandatória |
| :--- | :--- | :--- |
| *"Foi apenas uma edição pequena em um arquivo, não preciso rodar o gerador do ORGANIZATION.md."* | Quebra a sincronia do catálogo mestre e impede que outros agentes localizem o documento atualizado. | **Sempre** execute `python scripts/gerar_organization.py --write` após criar ou renomear qualquer `.mdx`. |
| *"O linter de PDF é só para quando formos imprimir, posso pular a validação com `--check-only`."* | Diagramas distorcidos ou títulos órfãos vazam silenciosamente para o acervo. | **Sempre** valide arquivos `.mdx` criados/editados com `python scripts/gerar_pdf.py "<arquivo.mdx>" --check-only`. |
| *"Vou criar um novo arquivo para este assunto porque a discussão de hoje é nova."* | Duplica o assunto, fragmenta o histórico e viola a Linha do Tempo Única (Regra 2 do `AGENTS.md`). | **Nunca** crie arquivos duplicados. Localize o `.mdx` existente e adicione uma nova entrada na seção `## Linha do Tempo`. |
| *"Posso usar `<b>` ou `<strong>` dentro do rótulo do nó do Mermaid para destacar o texto."* | Parsers MDX e compiladores de PDF renderizam essas tags como texto literal vazado (ex: `<b>Título</b>`). | **Proibição estrita**: Nunca use tags HTML em nós do Mermaid. Use texto em maiúsculas ou quebras `<br/>`. |
| *"Stakeholder Executivo é da área de negócios, mas vou incluir logs de erro e IPs para ficar mais detalhado."* | Gera ruído, confunde o stakeholder e viola a Diretriz 10 do `AGENTS.md`. | **Linguagem 100% de negócios**: Foco estrito em hotéis, chamados e impactos operacionais. Omitir termos técnicos de TI. |
| *"O teste mock passa, então não preciso testar com o código real."* | O mock pode mascarar falhas de contrato em tempo de execução. | **TDD Real**: O teste deve falhar antes da implementação e passar apenas com a execução real do código. |

---

## 3. Portão de Encerramento de Turno (Checklist Obrigatório)

Antes de concluir qualquer resposta onde arquivos `.mdx` ou scripts foram criados ou alterados, execute mentalmente e no terminal o seguinte portão:

- [ ] 1. O frontmatter YAML possui `title`, `category`, `tags`, `updatedAt` e `status` válidos? (`python scripts/validar_frontmatter.py`)
- [ ] 2. Existem links markdown quebrados no documento? (`python scripts/validar_links.py`)
- [ ] 3. Os diagramas Mermaid possuem menos de 4 ramificações horizontais e rótulos limpos? (`python scripts/gerar_pdf.py "<arquivo.mdx>" --check-only`)
- [ ] 4. O registro em `MEMORY.md` foi adicionado no topo do histórico com data e contexto?
- [ ] 5. O catálogo `ORGANIZATION.md` foi sincronizado? (`python scripts/gerar_organization.py --write`)
