import React from "react";

const envColors = {
  prd: { bg: "#fee2e2", text: "#991b1b", border: "#f87171" },
  prod: { bg: "#fee2e2", text: "#991b1b", border: "#f87171" },
  stg: { bg: "#fef3c7", text: "#92400e", border: "#fbbf24" },
  dev: { bg: "#e0e7ff", text: "#3730a3", border: "#818cf8" },
  all: { bg: "#f3f4f6", text: "#374151", border: "#d1d5db" },
};

/**
 * Componente visual para documentação de parâmetros, variáveis de ambiente (.env) e segredos.
 * @param {Array<{name: string, env: string, type: string, required: boolean, example: string, description: string}>} params
 */
export function ParamTable({ params = [] }) {
  return (
    <div style={{ margin: "1.5rem 0", overflowX: "auto" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "0.875rem",
          textAlign: "left",
          border: "1px solid #e5e7eb",
          borderRadius: "0.5rem",
          overflow: "hidden",
        }}
      >
        <thead>
          <tr
            style={{
              backgroundColor: "#f9fafb",
              borderBottom: "2px solid #e5e7eb",
            }}
          >
            <th
              style={{
                padding: "0.75rem 1rem",
                fontWeight: "600",
                color: "#374151",
              }}
            >
              Parâmetro / Chave
            </th>
            <th
              style={{
                padding: "0.75rem 1rem",
                fontWeight: "600",
                color: "#374151",
              }}
            >
              Ambiente
            </th>
            <th
              style={{
                padding: "0.75rem 1rem",
                fontWeight: "600",
                color: "#374151",
              }}
            >
              Tipo
            </th>
            <th
              style={{
                padding: "0.75rem 1rem",
                fontWeight: "600",
                color: "#374151",
              }}
            >
              Obrigatório
            </th>
            <th
              style={{
                padding: "0.75rem 1rem",
                fontWeight: "600",
                color: "#374151",
              }}
            >
              Valor de Exemplo
            </th>
            <th
              style={{
                padding: "0.75rem 1rem",
                fontWeight: "600",
                color: "#374151",
              }}
            >
              Descrição Técnica
            </th>
          </tr>
        </thead>
        <tbody>
          {params.map((item, index) => {
            const envKey = (item.env || "all").toLowerCase();
            const envStyle = envColors[envKey] || envColors.all;
            return (
              <tr
                key={index}
                style={{
                  borderBottom: "1px solid #f3f4f6",
                  backgroundColor: index % 2 === 0 ? "#ffffff" : "#fafafa",
                }}
              >
                <td
                  style={{
                    padding: "0.75rem 1rem",
                    fontFamily: "monospace",
                    fontWeight: "600",
                    color: "#0f172a",
                  }}
                >
                  {item.name}
                </td>
                <td style={{ padding: "0.75rem 1rem" }}>
                  <span
                    style={{
                      backgroundColor: envStyle.bg,
                      color: envStyle.text,
                      border: `1px solid ${envStyle.border}`,
                      padding: "0.15rem 0.45rem",
                      borderRadius: "0.25rem",
                      fontSize: "0.7rem",
                      fontWeight: "700",
                      textTransform: "uppercase",
                    }}
                  >
                    {item.env || "ALL"}
                  </span>
                </td>
                <td
                  style={{
                    padding: "0.75rem 1rem",
                    color: "#6b7280",
                    fontFamily: "monospace",
                    fontSize: "0.8rem",
                  }}
                >
                  {item.type || "string"}
                </td>
                <td style={{ padding: "0.75rem 1rem", textAlign: "center" }}>
                  {item.required ? (
                    <span style={{ color: "#dc2626", fontWeight: "bold" }}>
                      Sim
                    </span>
                  ) : (
                    <span style={{ color: "#6b7280" }}>Não</span>
                  )}
                </td>
                <td
                  style={{
                    padding: "0.75rem 1rem",
                    fontFamily: "monospace",
                    color: "#4b5563",
                    fontSize: "0.8rem",
                  }}
                >
                  {item.example ? (
                    <code
                      style={{
                        backgroundColor: "#f1f5f9",
                        padding: "0.2rem 0.4rem",
                        borderRadius: "0.25rem",
                      }}
                    >
                      {item.example}
                    </code>
                  ) : (
                    <span style={{ color: "#9ca3af" }}>—</span>
                  )}
                </td>
                <td
                  style={{
                    padding: "0.75rem 1rem",
                    color: "#374151",
                    lineHeight: "1.4",
                  }}
                >
                  {item.description}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default ParamTable;
