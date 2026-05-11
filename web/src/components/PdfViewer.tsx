import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import type { Citation } from "../api/client";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export function PdfViewer({
  url,
  highlight,
}: {
  url: string;
  highlight: Citation | null;
}) {
  const [numPages, setNumPages] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!highlight) return;
    const el = containerRef.current?.querySelector<HTMLElement>(`[data-page="${highlight.page}"]`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlight]);

  return (
    <div ref={containerRef} style={{ overflow: "auto", height: "calc(100vh - 80px)" }}>
      <Document file={url} onLoadSuccess={({ numPages }) => setNumPages(numPages)}>
        {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNumber) => (
          <div
            key={pageNumber}
            data-page={pageNumber}
            style={{ position: "relative", marginBottom: 16 }}
          >
            <Page pageNumber={pageNumber} width={640} />
            {highlight && highlight.page === pageNumber && (
              <CitationOverlay bbox={highlight.bbox} pageWidth={640} />
            )}
          </div>
        ))}
      </Document>
    </div>
  );
}

function CitationOverlay({
  bbox,
  pageWidth,
}: {
  bbox: [number, number, number, number];
  pageWidth: number;
}) {
  // Approximate: PDF coords are in points (72/inch). The page renders at `pageWidth`
  // pixels for some reference width (most PDFs ~612pt = 8.5in). For the demo we
  // assume 612pt → pageWidth scaling.
  const scale = pageWidth / 612;
  const [x0, y0, x1, y1] = bbox;
  return (
    <div
      style={{
        position: "absolute",
        left: x0 * scale,
        top: y0 * scale,
        width: (x1 - x0) * scale,
        height: (y1 - y0) * scale,
        background: "rgba(251, 191, 36, 0.35)",
        border: "1px solid #f59e0b",
        pointerEvents: "none",
      }}
    />
  );
}
