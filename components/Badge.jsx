import React from "react";

const colors = {
  ideia: { bg: "#e0e7ff", text: "#3730a3" },
  processo: { bg: "#fef3c7", text: "#92400e" },
  projeto: { bg: "#d1fae5", text: "#065f46" },
  trabalho: { bg: "#dbeafe", text: "#1e40af" },
  rpg: { bg: "#fce7f3", text: "#9d174d" },
  studiokustom: { bg: "#f3e8ff", text: "#6b21a8" },
  blue: { bg: "#dbeafe", text: "#1e40af" },
  red: { bg: "#fee2e2", text: "#991b1b" },
  purple: { bg: "#f3e8ff", text: "#6b21a8" },
  green: { bg: "#d1fae5", text: "#065f46" },
  yellow: { bg: "#fef3c7", text: "#92400e" },
  gray: { bg: "#f3f4f6", text: "#374151" },
  default: { bg: "#f3f4f6", text: "#374151" },
};

export function Badge({ label, type, variant, children }) {
  const chosenType = (variant || type || "default").toLowerCase();
  const style = colors[chosenType] || colors.default;
  const content = label || children;

  return (
    <span
      style={{
        backgroundColor: style.bg,
        color: style.text,
        padding: "0.2rem 0.6rem",
        borderRadius: "9999px",
        fontSize: "0.75rem",
        fontWeight: "600",
        display: "inline-block",
        marginRight: "0.4rem",
        verticalAlign: "middle",
      }}
    >
      {content}
    </span>
  );
}

export default Badge;
