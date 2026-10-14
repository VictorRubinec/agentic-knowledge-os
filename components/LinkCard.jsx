import React from "react";

export function LinkCard({ title, href, description, category }) {
  return (
    <a
      href={href}
      style={{
        textDecoration: "none",
        color: "inherit",
        display: "block",
        margin: "0.8rem 0",
      }}
    >
      <div
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: "0.5rem",
          padding: "1rem",
          backgroundColor: "#ffffff",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          transition: "border-color 0.2s",
        }}
      >
        {category && (
          <span
            style={{
              fontSize: "0.75rem",
              color: "#6b7280",
              textTransform: "uppercase",
              fontWeight: "bold",
            }}
          >
            {category}
          </span>
        )}
        <h4
          style={{ margin: "0.3rem 0", color: "#1d4ed8", fontSize: "1.05rem" }}
        >
          🔗 {title}
        </h4>
        {description && (
          <p style={{ margin: "0", fontSize: "0.9rem", color: "#4b5563" }}>
            {description}
          </p>
        )}
      </div>
    </a>
  );
}

export default LinkCard;
