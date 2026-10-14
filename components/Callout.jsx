import React from "react";

const presets = {
  info: { border: "#2563eb", bg: "#f0f9ff", text: "#0f172a", icon: "ℹ️" },
  warning: { border: "#d97706", bg: "#fffbeb", text: "#0f172a", icon: "⚠️" },
  success: { border: "#059669", bg: "#ecfdf5", text: "#0f172a", icon: "✅" },
  important: { border: "#dc2626", bg: "#fef2f2", text: "#0f172a", icon: "🚨" },
};

export function Callout({ title, type = "info", children }) {
  const style = presets[type] || presets.info;
  return (
    <div
      style={{
        borderLeft: `4px solid ${style.border}`,
        backgroundColor: style.bg,
        color: style.text,
        padding: "0.875rem 1rem",
        borderRadius: "0.375rem",
        margin: "1rem 0",
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
      }}
    >
      <style>{`.callout-body p { margin: 0 !important; display: inline !important; }`}</style>
      {title && (
        <div
          style={{
            fontWeight: "700",
            marginBottom: "0.35rem",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
            color: style.text,
            fontSize: "0.95rem",
          }}
        >
          <span>{style.icon}</span> <span>{title}</span>
        </div>
      )}
      <div
        className="callout-body"
        style={{ color: style.text, lineHeight: "1.5", fontSize: "0.9rem" }}
      >
        {children}
      </div>
    </div>
  );
}

export default Callout;
