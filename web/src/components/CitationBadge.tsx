import type { Citation } from "../api/client";

export function CitationBadge({
  citation,
  onHover,
}: {
  citation: Citation;
  onHover?: (c: Citation | null) => void;
}) {
  return (
    <span
      onMouseEnter={() => onHover?.(citation)}
      onMouseLeave={() => onHover?.(null)}
      style={{
        display: "inline-block",
        fontSize: 11,
        padding: "2px 6px",
        marginRight: 4,
        borderRadius: 4,
        background: "#eef2ff",
        color: "#3730a3",
        cursor: "help",
      }}
      title={citation.source_text}
    >
      p.{citation.page}
    </span>
  );
}
