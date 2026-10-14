import React from "react";

const statusColors = {
  sucesso: {
    border: "#10b981",
    badgeBg: "#d1fae5",
    badgeText: "#065f46",
    icon: "✅",
  },
  success: {
    border: "#10b981",
    badgeBg: "#d1fae5",
    badgeText: "#065f46",
    icon: "✅",
  },
  producao: {
    border: "#2563eb",
    badgeBg: "#dbeafe",
    badgeText: "#1e40af",
    icon: "🚀",
  },
  homologacao: {
    border: "#f59e0b",
    badgeBg: "#fef3c7",
    badgeText: "#92400e",
    icon: "🧪",
  },
  rollback: {
    border: "#ef4444",
    badgeBg: "#fee2e2",
    badgeText: "#991b1b",
    icon: "🔄",
  },
  falha: {
    border: "#dc2626",
    badgeBg: "#fee2e2",
    badgeText: "#991b1b",
    icon: "❌",
  },
  alinhamento: {
    border: "#8b5cf6",
    badgeBg: "#ede9fe",
    badgeText: "#5b21b6",
    icon: "📋",
  },
};

/**
 * Componente visual de Linha do Tempo Técnica de Deployments e Marcos Arquiteturais.
 * @param {Array<{
 *   date: string,
 *   version?: string,
 *   title: string,
 *   author?: string,
 *   status?: 'sucesso' | 'producao' | 'homologacao' | 'rollback' | 'falha' | 'alinhamento',
 *   commit?: string,
 *   summary: string,
 *   changes?: string[]
 * }>} releases
 */
export function DeploymentTimeline({ releases = [] }) {
  return (
    <div style={{ margin: "2rem 0", position: "relative" }}>
      {releases.map((release, index) => {
        const statusKey = (release.status || "sucesso").toLowerCase();
        const conf = statusColors[statusKey] || statusColors.sucesso;

        return (
          <div
            key={index}
            style={{
              display: "flex",
              gap: "1.25rem",
              position: "relative",
              paddingBottom: index === releases.length - 1 ? "0" : "1.75rem",
            }}
          >
            {/* Linha vertical conectora */}
            {index !== releases.length - 1 && (
              <div
                style={{
                  position: "absolute",
                  left: "11px",
                  top: "28px",
                  bottom: "0",
                  width: "2px",
                  backgroundColor: "#e5e7eb",
                }}
              />
            )}

            {/* Ponto indicador */}
            <div
              style={{
                width: "24px",
                height: "24px",
                borderRadius: "50%",
                backgroundColor: conf.border,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.75rem",
                color: "#ffffff",
                flexShrink: 0,
                zIndex: 1,
                boxShadow: "0 0 0 3px #ffffff",
              }}
            >
              •
            </div>

            {/* Conteúdo do Card de Deploy */}
            <div
              style={{
                flex: 1,
                backgroundColor: "#ffffff",
                border: "1px solid #e5e7eb",
                borderRadius: "0.5rem",
                padding: "1rem",
                boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "0.5rem",
                  marginBottom: "0.5rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  {release.version && (
                    <span
                      style={{
                        backgroundColor: "#1e293b",
                        color: "#f8fafc",
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        fontWeight: "700",
                        padding: "0.15rem 0.45rem",
                        borderRadius: "0.25rem",
                      }}
                    >
                      {release.version}
                    </span>
                  )}
                  <h4
                    style={{
                      margin: 0,
                      fontSize: "1rem",
                      fontWeight: "600",
                      color: "#0f172a",
                    }}
                  >
                    {release.title}
                  </h4>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <span
                    style={{
                      backgroundColor: conf.badgeBg,
                      color: conf.badgeText,
                      fontSize: "0.75rem",
                      fontWeight: "600",
                      padding: "0.15rem 0.5rem",
                      borderRadius: "9999px",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.25rem",
                    }}
                  >
                    {conf.icon} {release.status || "Sucesso"}
                  </span>
                  <span
                    style={{
                      fontSize: "0.8rem",
                      color: "#6b7280",
                      fontFamily: "monospace",
                    }}
                  >
                    {release.date}
                  </span>
                </div>
              </div>

              {/* Metadados: Autor e Commit */}
              {(release.author || release.commit) && (
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "#64748b",
                    marginBottom: "0.5rem",
                    display: "flex",
                    gap: "1rem",
                  }}
                >
                  {release.author && (
                    <span>
                      👤 Responsável: <strong>{release.author}</strong>
                    </span>
                  )}
                  {release.commit && (
                    <span>
                      🏷️ Ref:{" "}
                      <code
                        style={{
                          backgroundColor: "#f1f5f9",
                          padding: "0.1rem 0.3rem",
                          borderRadius: "0.2rem",
                        }}
                      >
                        {release.commit}
                      </code>
                    </span>
                  )}
                </div>
              )}

              <p
                style={{
                  margin: "0 0 0.5rem 0",
                  color: "#334155",
                  fontSize: "0.875rem",
                  lineHeight: "1.5",
                }}
              >
                {release.summary}
              </p>

              {release.changes && release.changes.length > 0 && (
                <ul
                  style={{
                    margin: "0",
                    paddingLeft: "1.25rem",
                    color: "#475569",
                    fontSize: "0.825rem",
                    lineHeight: "1.4",
                  }}
                >
                  {release.changes.map((ch, idx) => (
                    <li key={idx}>{ch}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default DeploymentTimeline;
