import { useState } from "react";
import type { Citation, Field } from "../api/client";
import { CitationBadge } from "./CitationBadge";

export function FieldEditor({
  field,
  onSave,
  onCitationHover,
}: {
  field: Field;
  onSave: (newValue: unknown, reason: string) => void;
  onCitationHover?: (c: Citation | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(String(field.value ?? ""));
  const [reason, setReason] = useState("");

  return (
    <div
      style={{
        padding: "10px 12px",
        border: "1px solid #e5e7eb",
        borderRadius: 6,
        marginBottom: 8,
      }}
    >
      <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 4 }}>
        {field.field_path} · confidence {field.confidence.toFixed(2)}
      </div>
      {editing ? (
        <>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            style={{ width: "100%", padding: 6, fontSize: 14 }}
          />
          <input
            placeholder="Reason for edit (optional)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            style={{ width: "100%", padding: 6, fontSize: 12, marginTop: 6 }}
          />
          <div style={{ marginTop: 6 }}>
            <button
              onClick={() => {
                onSave(value, reason);
                setEditing(false);
              }}
            >
              Save
            </button>
            <button onClick={() => setEditing(false)} style={{ marginLeft: 6 }}>
              Cancel
            </button>
          </div>
        </>
      ) : (
        <div
          onClick={() => setEditing(true)}
          style={{
            fontSize: 15,
            fontWeight: 500,
            cursor: "text",
            padding: "4px 0",
          }}
        >
          {String(field.value)}
        </div>
      )}
      <div style={{ marginTop: 6 }}>
        {field.citations.map((c, i) => (
          <CitationBadge key={i} citation={c} onHover={onCitationHover} />
        ))}
      </div>
    </div>
  );
}
