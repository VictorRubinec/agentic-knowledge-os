import React from "react";

const statusColors = {
  "em teste": { bg: "#fff7ed", border: "#f97316", text: "#c2410c", dot: "#ea580c" },
  "em review": { bg: "#fff7ed", border: "#f97316", text: "#c2410c", dot: "#ea580c" },
  "em desenvolvimento": { bg: "#ede9fe", border: "#8b5cf6", text: "#5b21b6", dot: "#7c3aed" },
  "em progresso": { bg: "#eff6ff", border: "#3b82f6", text: "#1e40af", dot: "#2563eb" },
  "aguardando aprovação": { bg: "#fef3c7", border: "#f59e0b", text: "#92400e", dot: "#d97706" },
  "aguardando gestor": { bg: "#fef3c7", border: "#f59e0b", text: "#92400e", dot: "#d97706" },
  "concluído": { bg: "#ecfdf5", border: "#10b981", text: "#065f46", dot: "#059669" },
  "homologação": { bg: "#f5f3ff", border: "#a855f7", text: "#6b21a8", dot: "#9333ea" },
  "backlog": { bg: "#f1f5f9", border: "#94a3b8", text: "#334155", dot: "#64748b" },
  default: { bg: "#f1f5f9", border: "#94a3b8", text: "#334155", dot: "#64748b" },
};

const priorityStyles = {
  urgent: { text: "Urgente", color: "#ef4444", bg: "#fef2f2" },
  urgente: { text: "Urgente", color: "#ef4444", bg: "#fef2f2" },
  high: { text: "Alta", color: "#f97316", bg: "#fff7ed" },
  alta: { text: "Alta", color: "#f97316", bg: "#fff7ed" },
  normal: { text: "Normal", color: "#3b82f6", bg: "#eff6ff" },
  low: { text: "Baixa", color: "#64748b", bg: "#f8fafc" },
  baixa: { text: "Baixa", color: "#64748b", bg: "#f8fafc" },
  default: { text: "Normal", color: "#3b82f6", bg: "#eff6ff" },
};

export function ClickUpTaskHeader({
  taskId,
  taskUrl,
  status = "Em Aberto",
  priority = "normal",
  list = "Geral",
  folder = "Portal",
  space = "Join4 | Squad NodeX",
  dueDate,
  assignee = "Victor Rubinec",
  tags = [],
}) {
  const normStatus = (status || "default").toLowerCase().trim();
  const stStyle = statusColors[normStatus] || statusColors.default;

  const normPriority = (priority || "normal").toLowerCase().trim();
  const prStyle = priorityStyles[normPriority] || priorityStyles.default;

  const url = taskUrl || (taskId ? `https://app.clickup.com/t/${taskId}` : "#");

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "0.625rem",
        padding: "1rem 1.25rem",
        margin: "1.25rem 0",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)",
      }}
    >
      {/* Top Bar: Breadcrumb + ClickUp Action Link */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.5rem",
          paddingBottom: "0.75rem",
          marginBottom: "0.75rem",
          borderBottom: "1px solid #f1f5f9",
          fontSize: "0.78rem",
          color: "#64748b",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <span style={{ fontWeight: "600", color: "#475569" }}>Join4 Produtos</span>
          <span>/</span>
          {folder && <span>{folder}</span>}
          {folder && <span>/</span>}
          <span style={{ fontWeight: "600", color: "#0f172a" }}>{list}</span>
          {taskId && (
            <span
              style={{
                marginLeft: "0.4rem",
                fontFamily: "monospace",
                backgroundColor: "#f1f5f9",
                color: "#475569",
                padding: "0.15rem 0.4rem",
                borderRadius: "0.25rem",
                fontSize: "0.72rem",
              }}
            >
              #{taskId}
            </span>
          )}
        </div>

        {taskId && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.3rem",
              color: "#7b68ee",
              fontWeight: "600",
              textDecoration: "none",
              fontSize: "0.75rem",
              padding: "0.2rem 0.5rem",
              borderRadius: "0.375rem",
              backgroundColor: "#f5f3ff",
              border: "1px solid #ddd6fe",
            }}
          >
            <span>Abrir no ClickUp</span>
            <span style={{ fontSize: "0.7rem" }}>↗</span>
          </a>
        )}
      </div>

      {/* Main Metadata Grid */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "0.75rem 1.25rem",
          fontSize: "0.82rem",
        }}
      >
        {/* Status Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <span style={{ color: "#64748b", fontSize: "0.75rem", fontWeight: "500" }}>Status:</span>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.35rem",
              backgroundColor: stStyle.bg,
              border: `1px solid ${stStyle.border}`,
              color: stStyle.text,
              padding: "0.2rem 0.6rem",
              borderRadius: "9999px",
              fontWeight: "600",
              fontSize: "0.75rem",
              textTransform: "uppercase",
              letterSpacing: "0.02em",
            }}
          >
            <span
              style={{
                width: "0.45rem",
                height: "0.45rem",
                borderRadius: "50%",
                backgroundColor: stStyle.dot,
                display: "inline-block",
              }}
            />
            {status}
          </span>
        </div>

        {/* Priority Badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <span style={{ color: "#64748b", fontSize: "0.75rem", fontWeight: "500" }}>Prioridade:</span>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.25rem",
              backgroundColor: prStyle.bg,
              color: prStyle.color,
              padding: "0.2rem 0.5rem",
              borderRadius: "0.25rem",
              fontWeight: "600",
              fontSize: "0.75rem",
            }}
          >
            <span>🚩</span>
            {prStyle.text}
          </span>
        </div>

        {/* Assignee */}
        {assignee && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ color: "#64748b", fontSize: "0.75rem", fontWeight: "500" }}>Responsável:</span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                padding: "0.15rem 0.5rem",
                borderRadius: "9999px",
                fontWeight: "500",
                color: "#1e293b",
                fontSize: "0.75rem",
              }}
            >
              <span
                style={{
                  width: "1.1rem",
                  height: "1.1rem",
                  borderRadius: "50%",
                  backgroundColor: "#795548",
                  color: "#ffffff",
                  fontSize: "0.6rem",
                  fontWeight: "700",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                VR
              </span>
              {assignee}
            </span>
          </div>
        )}

        {/* Due Date */}
        {dueDate && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ color: "#64748b", fontSize: "0.75rem", fontWeight: "500" }}>Prazo:</span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                backgroundColor: "#fff7ed",
                color: "#c2410c",
                border: "1px solid #fed7aa",
                padding: "0.15rem 0.5rem",
                borderRadius: "0.25rem",
                fontWeight: "600",
                fontSize: "0.75rem",
              }}
            >
              <span>📅</span>
              {dueDate}
            </span>
          </div>
        )}

        {/* Tags */}
        {tags && tags.length > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", flexWrap: "wrap" }}>
            {tags.map((tag, idx) => (
              <span
                key={idx}
                style={{
                  backgroundColor: "#f1f5f9",
                  color: "#475569",
                  padding: "0.15rem 0.45rem",
                  borderRadius: "0.25rem",
                  fontSize: "0.7rem",
                  fontWeight: "500",
                }}
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ClickUpTaskHeader;
