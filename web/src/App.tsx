import { Link, Outlet } from "react-router-dom";

export function App() {
  return (
    <div style={{ fontFamily: "system-ui, sans-serif" }}>
      <header
        style={{
          padding: "12px 20px",
          borderBottom: "1px solid #ddd",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Link to="/queue" style={{ textDecoration: "none", color: "#111", fontWeight: 600 }}>
          AI Document Processing
        </Link>
        <span style={{ color: "#666", fontSize: 13 }}>
          dev: reviewer@demo
        </span>
      </header>
      <main style={{ padding: 20 }}>
        <Outlet />
      </main>
    </div>
  );
}
