import React from "react";

const statusColors = {
  "em teste": { bg: "#fff7ed", border: "#f97316", text: "#c2410c", bar: "#ea580c" },
  "em review": { bg: "#fff7ed", border: "#f97316", text: "#c2410c", bar: "#ea580c" },
  "em desenvolvimento": { bg: "#ede9fe", border: "#8b5cf6", text: "#5b21b6", bar: "#7c3aed" },
  "em progresso": { bg: "#eff6ff", border: "#3b82f6", text: "#1e40af", bar: "#2563eb" },
  "aguardando aprovação": { bg: "#fef3c7", border: "#f59e0b", text: "#92400e", bar: "#d97706" },
  "aguardando gestor": { bg: "#fef3c7", border: "#f59e0b", text: "#92400e", bar: "#d97706" },
  "concluído": { bg: "#ecfdf5", border: "#10b981", text: "#065f46", bar: "#059669" },
  "homologação": { bg: "#f5f3ff", border: "#a855f7", text: "#6b21a8", bar: "#9333ea" },
  "backlog": { bg: "#f1f5f9", border: "#94a3b8", text: "#334155", bar: "#64748b" },
  default: { bg: "#f1f5f9", border: "#94a3b8", text: "#334155", bar: "#64748b" },
};

const priorityStyles = {
  urgent: { text: "Urgente", color: "#ef4444" },
  urgente: { text: "Urgente", color: "#ef4444" },
  high: { text: "Alta", color: "#f97316" },
  alta: { text: "Alta", color: "#f97316" },
  normal: { text: "Normal", color: "#3b82f6" },
  low: { text: "Baixa", color: "#64748b" },
  baixa: { text: "Baixa", color: "#64748b" },
  default: { text: "Normal", color: "#3b82f6" },
};

export function ClickUpTaskCard({
  code,
  title,
  href,
  clickupId,
  clickupUrl,
  status = "Backlog",
  priority = "normal",
  folder = "Portal",
  list = "ETL",
  dueDate,
  assignee = "Victor Rubinec",
  progress, // e.g. { completed: 3, total: 4 }
}) {
  const normStatus = (status || "default").toLowerCase().trim();
  const stStyle = statusColors[normStatus] || statusColors.default;

  const normPriority = (priority || "normal").toLowerCase().trim();
  const prStyle = priorityStyles[normPriority] || priorityStyles.default;

  const pct =
    progress && progress.total > 0
      ? Math.round((progress.completed / progress.total) * 100)
      : null;

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        border: "1px solid #e2e8f0",
        borderLeft: `4px solid ${stStyle.bar}`,
        borderRadius: "0.5rem",
        padding: "0.875rem 1.15rem",
        margin: "0.65rem 0",
        boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)",
        transition: "box-shadow 0.2s ease",
      }}
    >
      {/* Top row: Code + Breadcrumbs + ClickUp link */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.4rem",
          fontSize: "0.75rem",
          color: "#64748b",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          {code && (
            <span
              style={{
                fontWeight: "700",
                fontFamily: "monospace",
                color: "#1e293b",
                backgroundColor: "#f1f5f9",
                padding: "0.1rem 0.35rem",
                borderRadius: "0.25rem",
              }}
            >
              {code}
            </span>
          )}
          <span>
            {folder} / {list}
          </span>
          {clickupId && (
            <span style={{ fontFamily: "monospace", color: "#94a3b8" }}>
              (#{clickupId})
            </span>
          )}
        </div>

        {clickupUrl && (
          <a
            href={clickupUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: "none",
              color: "#7b68ee",
              fontWeight: "600",
              fontSize: "0.72rem",
            }}
          >
            ClickUp ↗
          </a>
        )}
      </div>

      {/* Title */}
      <div style={{ marginBottom: "0.65rem" }}>
        <a
          href={href || "#"}
          style={{
            fontSize: "0.95rem",
            fontWeight: "600",
            color: "#0f172a",
            textDecoration: "none",
            lineHeight: "1.35",
          }}
        >
          {title}
        </a>
      </div>

      {/* Bottom metadata row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.5rem",
          fontSize: "0.75rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          {/* Status Pill */}
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.25rem",
              backgroundColor: stStyle.bg,
              border: `1px solid ${stStyle.border}`,
              color: stStyle.text,
              padding: "0.15rem 0.45rem",
              borderRadius: "9999px",
              fontWeight: "600",
              fontSize: "0.7rem",
              textTransform: "uppercase",
            }}
          >
            <span
              style={{
                width: "0.4rem",
                height: "0.4rem",
                borderRadius: "50%",
                backgroundColor: stStyle.bar,
                display: "inline-block",
              }}
            />
            {status}
          </span>

          {/* Priority */}
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.2rem",
              color: prStyle.color,
              fontWeight: "600",
            }}
          >
            <span>🚩</span>
            {prStyle.text}
          </span>

          {/* Due date */}
          {dueDate && (
            <span style={{ color: "#64748b" }}>
              📅 {dueDate}
            </span>
          )}
        </div>

        {/* Right side: Assignee & Optional Progress */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {pct !== null && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <div
                style={{
                  width: "50px",
                  height: "5px",
                  backgroundColor: "#f1f5f9",
                  borderRadius: "9999px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: "100%",
                    backgroundColor: pct === 100 ? "#10b981" : "#7b68ee",
                  }}
                />
              </div>
              <span style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: "600" }}>
                {progress.completed}/{progress.total}
              </span>
            </div>
          )}

          {assignee && (
            <span
              style={{
                width: "1.25rem",
                height: "1.25rem",
                borderRadius: "50%",
                backgroundColor: "#795548",
                color: "#ffffff",
                fontSize: "0.62rem",
                fontWeight: "700",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
              }}
              title={assignee}
            >
              VR
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default ClickUpTaskCard;
