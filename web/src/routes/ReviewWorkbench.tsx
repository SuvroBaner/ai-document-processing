import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api, type Citation, type ReviewPayload } from "../api/client";
import { PdfViewer } from "../components/PdfViewer";
import { FieldEditor } from "../components/FieldEditor";
import { STATE_LABEL } from "../lib/workflow";

export function ReviewWorkbench() {
  const { documentId } = useParams<{ documentId: string }>();
  const qc = useQueryClient();
  const [hover, setHover] = useState<Citation | null>(null);

  const { data, isLoading, error } = useQuery<ReviewPayload>({
    queryKey: ["review", documentId],
    queryFn: () => api.review(documentId!),
    enabled: !!documentId,
  });

  const patch = useMutation({
    mutationFn: (vars: { fieldId: string; newValue: unknown; reason: string }) =>
      api.patchField(documentId!, vars.fieldId, { new_value: vars.newValue, reason: vars.reason }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["review", documentId] }),
  });

  const approve = useMutation({
    mutationFn: () => api.approve(documentId!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["review", documentId] }),
  });

  if (isLoading) return <p>Loading…</p>;
  if (error || !data) return <p style={{ color: "red" }}>Failed: {String(error)}</p>;

  const state = data.document.state;
  const canApprove = state === "IN_REVIEW";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 24 }}>
      <div>
        <h2 style={{ fontSize: 16, margin: 0 }}>{data.document.filename}</h2>
        <PdfViewer url={data.document.pdf_url} highlight={hover} />
      </div>
      <aside>
        <div style={{ marginBottom: 12, fontSize: 13, color: "#374151" }}>
          State: <strong>{STATE_LABEL[state as keyof typeof STATE_LABEL] ?? state}</strong>
        </div>
        {data.extraction ? (
          <>
            {data.extraction.fields.map((f) => (
              <FieldEditor
                key={f.id}
                field={f}
                onSave={(v, r) => patch.mutate({ fieldId: f.id, newValue: v, reason: r })}
                onCitationHover={setHover}
              />
            ))}
            <button
              disabled={!canApprove || approve.isPending}
              onClick={() => approve.mutate()}
              style={{
                width: "100%",
                marginTop: 12,
                padding: "10px 14px",
                fontSize: 14,
                background: canApprove ? "#16a34a" : "#9ca3af",
                color: "white",
                border: 0,
                borderRadius: 6,
                cursor: canApprove ? "pointer" : "not-allowed",
              }}
            >
              {approve.isPending ? "Approving…" : "Approve"}
            </button>
          </>
        ) : (
          <p style={{ color: "#6b7280" }}>No extraction yet.</p>
        )}
      </aside>
    </div>
  );
}
