---
name: dbx-mcp
description: Guia operacional do servidor MCP do DBX (t8y2/dbx) para conexão segura, inspeção de schemas e consultas SQL com agentes autônomos.
allowed-tools: Bash(*)
---

# DBX Database Client & MCP Server (`dbx-mcp`)

Este guia instrui os agentes de IA sobre como utilizar e operar a integração MCP do **DBX** ([github.com/t8y2/dbx](https://github.com/t8y2/dbx)) para conectar com bancos de dados relacionais, NoSQL e analíticos.

---

## 1. Visão Geral

O **DBX** é um cliente de banco de dados universal construído em Rust e Tauri 2 (~25 MB). Ele expõe um **Model Context Protocol (MCP) Server** nativo (`@dbx-app/mcp-server`), permitindo que agentes de IA inspecionem schemas e executem consultas sem que credenciais de produção precisem ser expostas em texto puro.

---

## 2. Configuração do Servidor MCP

No arquivo de configuração de MCP dos agentes (`~/.gemini/config/mcp_config.json`, `.cursor/mcp.json` ou Claude Desktop):

```json
{
  "mcpServers": {
    "dbx": {
      "command": "npx",
      "args": ["-y", "@dbx-app/mcp-server"]
    }
  }
}
```

### Configuração com Backend Web / Docker:
Se o DBX estiver rodando em container Docker ou na Shard Cloud:
```json
{
  "mcpServers": {
    "dbx": {
      "command": "npx",
      "args": ["-y", "@dbx-app/mcp-server"],
      "env": {
        "DBX_WEB_URL": "http://localhost:4224",
        "DBX_WEB_PASSWORD": "sua-senha-do-painel"
      }
    }
  }
}
```

---

## 3. Diretrizes de Segurança (Gating Mandatório)

Os agentes de IA DEVEM respeitar rigorosamente as políticas de execução:

1. **Escopo Padrão Read-Only**:
   - Para inspeção, formulação de queries e auditoria, mantenha sempre o modo `read_only` ativado na interface do DBX (`Settings -> MCP`).
   - Bloqueia mutações acidentais (`DROP`, `TRUNCATE`, `DELETE`, `UPDATE`) em bases ativas.
2. **Inspeção de Schemas Antes de Execução**:
   - Sempre consulte a estrutura de tabelas, chaves primárias e tipos antes de gerar código SQL. Isso evita erros de compilação de query e alucinações de campos.
3. **Mutações Críticas (`safe_write` e `high_risk_write`)**:
   - Só execute scripts DDL (`ALTER`, `CREATE`) ou de carga quando explicitamente solicitado pelo usuário, apresentando sempre o comando SQL completo para validação prévia.
