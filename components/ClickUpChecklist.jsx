import React from "react";

export function ClickUpChecklist({
  title = "Checklist de Execução & Critérios de Aceite",
  items = [],
}) {
  const normalizedItems = items.map((it) => {
    if (typeof it === "string") {
      const isDone = it.startsWith("[x]") || it.startsWith("[X]");
      const cleanText = it.replace(/^\[[ xX]\]\s*/, "");
      return { text: cleanText, done: isDone };
    }
    return it;
  });

  const total = normalizedItems.length;
  const completed = normalizedItems.filter((it) => it.done).length;
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  const isAllDone = total > 0 && completed === total;

  const barColor = isAllDone ? "#10b981" : "#7b68ee";

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "0.5rem",
        padding: "1rem 1.25rem",
        margin: "1rem 0",
        boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)",
      }}
    >
      {/* Header with Title, Counter and Progress Bar */}
      <div style={{ marginBottom: "0.85rem" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "0.45rem",
          }}
        >
          <div
            style={{
              fontWeight: "700",
              color: "#0f172a",
              fontSize: "0.95rem",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <span style={{ fontSize: "1rem" }}>☑️</span>
            <span>{title}</span>
          </div>

          <div
            style={{
              fontSize: "0.78rem",
              fontWeight: "600",
              color: isAllDone ? "#059669" : "#64748b",
              backgroundColor: isAllDone ? "#ecfdf5" : "#f1f5f9",
              padding: "0.15rem 0.5rem",
              borderRadius: "9999px",
            }}
          >
            {completed}/{total} ({percentage}%)
          </div>
        </div>

        {/* Progress Bar Track */}
        <div
          style={{
            width: "100%",
            height: "6px",
            backgroundColor: "#f1f5f9",
            borderRadius: "9999px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${percentage}%`,
              height: "100%",
              backgroundColor: barColor,
              borderRadius: "9999px",
              transition: "width 0.3s ease",
            }}
          />
        </div>
      </div>

      {/* Items List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {normalizedItems.map((item, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.6rem",
              fontSize: "0.86rem",
              lineHeight: "1.45",
              color: item.done ? "#94a3b8" : "#1e293b",
              padding: "0.25rem 0",
            }}
          >
            {/* Custom Checkbox Circle */}
            <div
              style={{
                marginTop: "0.15rem",
                width: "1.1rem",
                height: "1.1rem",
                borderRadius: "50%",
                border: item.done ? "1px solid #10b981" : "1.5px solid #cbd5e1",
                backgroundColor: item.done ? "#10b981" : "#ffffff",
                color: "#ffffff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.65rem",
                fontWeight: "700",
                flexShrink: 0,
              }}
            >
              {item.done ? "✓" : ""}
            </div>

            {/* Text & Optional Tag */}
            <div style={{ flex: 1 }}>
              <span
                style={{
                  textDecoration: item.done ? "line-through" : "none",
                }}
              >
                {item.text}
              </span>

              {item.tag && (
                <span
                  style={{
                    marginLeft: "0.45rem",
                    fontSize: "0.7rem",
                    fontWeight: "600",
                    padding: "0.1rem 0.35rem",
                    borderRadius: "0.25rem",
                    backgroundColor: "#f1f5f9",
                    color: "#475569",
                  }}
                >
                  {item.tag}
                </span>
              )}

              {item.note && (
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "#64748b",
                    marginTop: "0.2rem",
                  }}
                >
                  {item.note}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ClickUpChecklist;
