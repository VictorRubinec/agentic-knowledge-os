import React from "react";

/**
 * Componente visual de Linha do Tempo para arquivos MDX.
 * @param {Array<{date: string, title: string, content: string, status?: string}>} items
 */
export function Timeline({ items, events }) {
  const list = events || items || [];
  return (
    <div
      style={{
        margin: "1.5rem 0",
        paddingLeft: "1rem",
        borderLeft: "3px solid #3b82f6",
      }}
    >
      {list.map((item, index) => (
        <div
          key={index}
          style={{ marginBottom: "1.2rem", position: "relative" }}
        >
          <div
            style={{
              fontSize: "0.85rem",
              fontWeight: "bold",
              color: "#3b82f6",
              textTransform: "uppercase",
            }}
          >
            📅 {item.date} {item.status ? `• [${item.status}]` : ""}
          </div>
          <h4 style={{ margin: "0.2rem 0", fontSize: "1.1rem" }}>
            {item.title}
          </h4>
          <p
            style={{ margin: "0.3rem 0", color: "#4b5563", lineHeight: "1.5" }}
          >
            {item.description || item.content}
          </p>
        </div>
      ))}
    </div>
  );
}

export default Timeline;
