import React from "react";

export function ClickUpActivityFeed({ activities = [] }) {
  if (!activities || activities.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        position: "relative",
        paddingLeft: "1.75rem",
        margin: "1.25rem 0",
      }}
    >
      {/* Vertical timeline connector track */}
      <div
        style={{
          position: "absolute",
          top: "1rem",
          bottom: "1rem",
          left: "0.75rem",
          width: "2px",
          backgroundColor: "#e2e8f0",
        }}
      />

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {activities.map((act, idx) => {
          const isBot = act.type === "bot";
          const avatarBg = isBot ? "#7b68ee" : "#795548";
          const avatarIcon = isBot ? "🤖" : "VR";
          const authorName = act.author || (isBot ? "Agente de Engenharia Join4" : "Victor Rubinec");

          return (
            <div key={idx} style={{ position: "relative" }}>
              {/* Avatar marker on the track */}
              <div
                style={{
                  position: "absolute",
                  left: "-1.75rem",
                  top: "0.25rem",
                  width: "1.5rem",
                  height: "1.5rem",
                  borderRadius: "50%",
                  backgroundColor: avatarBg,
                  color: "#ffffff",
                  fontSize: isBot ? "0.85rem" : "0.62rem",
                  fontWeight: "700",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 0 0 3px #ffffff",
                  zIndex: 2,
                }}
              >
                {avatarIcon}
              </div>

              {/* Activity Card Bubble */}
              <div
                style={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "0.5rem",
                  padding: "0.75rem 1rem",
                  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)",
                }}
              >
                {/* Header */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "0.35rem",
                    marginBottom: "0.4rem",
                    fontSize: "0.78rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    <span style={{ fontWeight: "700", color: "#0f172a" }}>
                      {authorName}
                    </span>
                    {isBot && (
                      <span
                        style={{
                          backgroundColor: "#f5f3ff",
                          color: "#7c3aed",
                          border: "1px solid #ddd6fe",
                          padding: "0.05rem 0.35rem",
                          borderRadius: "0.25rem",
                          fontSize: "0.65rem",
                          fontWeight: "600",
                        }}
                      >
                        IA Automação
                      </span>
                    )}
                    {act.badge && (
                      <span
                        style={{
                          backgroundColor: "#fff7ed",
                          color: "#c2410c",
                          border: "1px solid #fed7aa",
                          padding: "0.05rem 0.35rem",
                          borderRadius: "0.25rem",
                          fontSize: "0.65rem",
                          fontWeight: "600",
                        }}
                      >
                        {act.badge}
                      </span>
                    )}
                  </div>

                  {act.date && (
                    <span style={{ color: "#94a3b8", fontSize: "0.72rem" }}>
                      {act.date}
                    </span>
                  )}
                </div>

                {/* Optional Title */}
                {act.title && (
                  <div
                    style={{
                      fontWeight: "600",
                      color: "#1e293b",
                      fontSize: "0.86rem",
                      marginBottom: "0.25rem",
                    }}
                  >
                    {act.title}
                  </div>
                )}

                {/* Content */}
                <div
                  style={{
                    fontSize: "0.82rem",
                    color: "#334155",
                    lineHeight: "1.45",
                  }}
                >
                  {act.content}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ClickUpActivityFeed;
