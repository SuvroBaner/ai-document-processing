import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, type QueueItem } from "../api/client";
import { STATE_LABEL } from "../lib/workflow";

export function DocumentsList() {
  const { data, isLoading, error } = useQuery<QueueItem[]>({
    queryKey: ["queue"],
    queryFn: api.queue,
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p style={{ color: "red" }}>Failed: {String(error)}</p>;

  return (
    <div>
      <h1 style={{ fontSize: 18 }}>Review queue</h1>
      <table style={{ borderCollapse: "collapse", marginTop: 12 }}>
        <thead>
          <tr style={{ textAlign: "left", color: "#6b7280", fontSize: 12 }}>
            <th style={{ padding: "6px 12px" }}>Document</th>
            <th style={{ padding: "6px 12px" }}>Kind</th>
            <th style={{ padding: "6px 12px" }}>State</th>
          </tr>
        </thead>
        <tbody>
          {(data ?? []).map((d) => (
            <tr key={d.id} style={{ borderTop: "1px solid #eee" }}>
              <td style={{ padding: "8px 12px" }}>
                <Link to={`/review/${d.id}`}>{d.filename}</Link>
              </td>
              <td style={{ padding: "8px 12px" }}>{d.kind}</td>
              <td style={{ padding: "8px 12px" }}>{STATE_LABEL[d.state as keyof typeof STATE_LABEL] ?? d.state}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
