import { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";

const STATUS = { IDLE: "idle", LOADING: "loading", SUCCESS: "success", ERROR: "error" };

export default function AgentDataScientist() {
  const [uploadStatus, setUploadStatus] = useState({ type: STATUS.IDLE, message: "" });
  const [insightsStatus, setInsightsStatus] = useState({ type: STATUS.IDLE, message: "" });
  const [uploadResult, setUploadResult] = useState(null);
  const [insights, setInsights] = useState("");
  const [previewData, setPreviewData] = useState(null);
  const [insightsReady, setInsightsReady] = useState(false);
  const fileInputRef = useRef(null);
  const [analysisCode, setAnalysisCode] = useState("");
  const [plots, setPlots] = useState([]);
  const [consoleOutput, setConsoleOutput] = useState("");
  const [vizStatus, setVizStatus] = useState({ type: STATUS.IDLE, message: "" });

  async function uploadCSV() {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setUploadStatus({ type: STATUS.ERROR, message: "Please select a CSV file first." });
      return;
    }

    setUploadStatus({ type: STATUS.LOADING, message: "Uploading..." });
    setUploadResult(null);
    setInsightsReady(false);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/upload", { method: "POST", body: formData });
      const text = await res.text();

      let data;
      try { data = JSON.parse(text); }
      catch { throw new Error("Server returned non-JSON: " + text.slice(0, 200)); }

      if (!res.ok) throw new Error(data.detail || "Upload failed.");

      setPreviewData(data.raw_data_preview.preview);
      setUploadResult(data);
      setUploadStatus({
        type: STATUS.SUCCESS,
        message: `Uploaded: ${data.raw_data_preview.filename} — ${data.raw_data_preview.shape[0]} rows × ${data.raw_data_preview.shape[1]} cols`,
      });
      setInsightsReady(true);
      setInsightsStatus({ type: STATUS.IDLE, message: "Ready to generate insights." });
    } catch (err) {
      setUploadStatus({ type: STATUS.ERROR, message: "Error: " + err.message });
    }
  }

  async function generateInsights() {
    if (!previewData) return;

    setInsightsStatus({ type: STATUS.LOADING, message: "Generating insights… this may take a moment." });
    setInsights("");

    try {
      const res = await fetch("/generate-insights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preview: previewData }),
      });

      const text = await res.text();

      let data;
      try { data = JSON.parse(text); }
      catch { throw new Error("Server returned non-JSON: " + text.slice(0, 300)); }

      if (!res.ok) throw new Error(data.detail || "Insights generation failed.");

      setInsights(data.insights);
      setInsightsStatus({ type: STATUS.SUCCESS, message: "Insights generated." });
    } catch (err) {
      setInsightsStatus({ type: STATUS.ERROR, message: "Error: " + err.message });
    }
  }
// generating code and running it are now separate steps, since running the code can take a while and we want to show the generated code to the user before they run it
  async function generateAndRunAnalysis() {
  if (!previewData) return;
  setVizStatus({ type: STATUS.LOADING, message: "Generating and running EDA code..." });
  setPlots([]);

  try {
    // Step 1: get the code
    const codeRes = await fetch("/generate-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ schema_info: uploadResult.raw_data_preview }),
    });
    const codeData = await codeRes.json();
    setAnalysisCode(codeData.generated_code);

    // Step 2: run it
    const runRes = await fetch("/run-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: codeData.generated_code, preview: previewData }),
    });
    //Adding lines for debugging server response issues
    const rawText = await runRes.text();
    console.log("RAW RESPONSE:", rawText);

    const runData = JSON.parse(rawText);
    if (runData.exec_error) {
    setVizStatus({ type: STATUS.ERROR, message: `Code error: ${runData.exec_error}` });
    } else {
    setPlots(runData.plots ?? []);
    setConsoleOutput(runData.console);
    setVizStatus({ type: STATUS.SUCCESS, message: `Generated ${runData.plots.length} plots.` });
}

  } catch (err) {
    setVizStatus({ type: STATUS.ERROR, message: "Error: " + err.message });
  }
}

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.badge}>AI</div>
        <div>
          <h1 style={styles.h1}>Agent Data Scientist</h1>
          <p style={styles.subtitle}>Upload a CSV and let local AI generate EDA code and statistical insights</p>
        </div>
      </header>

      {/* Step 1 */}
      <section style={styles.card}>
        <StepLabel number={1} />
        <h2 style={styles.cardTitle}>Upload CSV</h2>

        <div style={styles.fileRow}>
          <label style={styles.fileLabel}>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              style={{ display: "none" }}
              onChange={() => {
                setUploadStatus({ type: STATUS.IDLE, message: "" });
                setUploadResult(null);
                setInsightsReady(false);
              }}
            />
            <span style={styles.fileButton}>Choose File</span>
            <span style={styles.fileName}>
              {fileInputRef.current?.files?.[0]?.name || "No file selected"}
            </span>
          </label>
          <button
            style={styles.btn}
            onClick={uploadCSV}
            disabled={uploadStatus.type === STATUS.LOADING}
          >
            {uploadStatus.type === STATUS.LOADING ? "Uploading…" : "Upload"}
          </button>
        </div>

        {uploadStatus.message && (
          <p style={{ ...styles.status, color: uploadStatus.type === STATUS.ERROR ? "#ef4444" : uploadStatus.type === STATUS.SUCCESS ? "#10b981" : "#6b7280" }}>
            {uploadStatus.message}
          </p>
        )}

        {uploadResult && (
          <pre style={styles.pre}>{JSON.stringify(uploadResult, null, 2)}</pre>
        )}
      </section>

      {/* Step 2 */}
      <section style={styles.card}>
        <StepLabel number={2} />
        <h2 style={styles.cardTitle}>Generate Insights</h2>
        <p style={styles.hint}>Upload a CSV first, then click below to run the AI insights report.</p>

        <button
          style={{ ...styles.btn, opacity: insightsReady ? 1 : 0.5 }}
          onClick={generateInsights}
          disabled={!insightsReady || insightsStatus.type === STATUS.LOADING}
        >
          {insightsStatus.type === STATUS.LOADING ? "Generating…" : "Generate Insights"}
        </button>

        {insightsStatus.message && (
          <p style={{ ...styles.status, color: insightsStatus.type === STATUS.ERROR ? "#ef4444" : insightsStatus.type === STATUS.SUCCESS ? "#10b981" : "#6b7280" }}>
            {insightsStatus.message}
          </p>
        )}

        {insights && (
          <div style={styles.insightsBox}>
            <ReactMarkdown>{insights}</ReactMarkdown>
          </div>
        )}
      </section>

      {/* Step 3 */}
<section style={styles.card}>
  <StepLabel number={3} />
  <h2 style={styles.cardTitle}>EDA Visualizations</h2>
  <p style={styles.hint}>Generate and run EDA code to see charts and statistics.</p>

  <button
    style={{ ...styles.btn, opacity: insightsReady ? 1 : 0.5 }}
    onClick={generateAndRunAnalysis}
    disabled={!insightsReady || vizStatus.type === STATUS.LOADING}
  >
    {vizStatus.type === STATUS.LOADING ? "Running…" : "Generate & Run EDA"}
  </button>

  {vizStatus.message && (
    <p style={{ ...styles.status, color: vizStatus.type === STATUS.ERROR ? "#ef4444" : vizStatus.type === STATUS.SUCCESS ? "#10b981" : "#6b7280" }}>
      {vizStatus.message}
    </p>
  )}

  {analysisCode && (
    <details style={{ marginTop: 14 }}>
      <summary style={{ cursor: "pointer", fontSize: "0.88rem", color: "#2563eb" }}>View generated code</summary>
      <pre style={styles.pre}>{analysisCode}</pre>
    </details>
  )}

  {consoleOutput && (
    <pre style={{ ...styles.pre, marginTop: 14 }}>{consoleOutput}</pre>
  )}

  {plots.map((b64, i) => (
    <img
      key={i}
      src={`data:image/png;base64,${b64}`}
      alt={`EDA plot ${i + 1}`}
      style={{ width: "100%", borderRadius: 8, marginTop: 16, border: "1px solid #e2e8f0" }}
    />
  ))}
</section>
    </div>
  );
}

function StepLabel({ number }) {
  return (
    <div style={styles.stepLabel}>
      <span style={styles.stepNum}>{number}</span>
      <span style={styles.stepText}>Step {number}</span>
    </div>
  );
}

const styles = {
  page: {
    fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
    maxWidth: 860,
    margin: "40px auto",
    padding: "0 20px",
    background: "#f8fafc",
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    marginBottom: 32,
  },
  badge: {
    background: "#2563eb",
    color: "white",
    fontWeight: 700,
    fontSize: "1.1rem",
    borderRadius: 10,
    width: 48,
    height: 48,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    letterSpacing: 1,
  },
  h1: {
    margin: 0,
    fontSize: "1.7rem",
    color: "#0f172a",
    fontWeight: 700,
  },
  subtitle: {
    margin: "4px 0 0",
    color: "#64748b",
    fontSize: "0.92rem",
  },
  card: {
    background: "white",
    border: "1px solid #e2e8f0",
    borderRadius: 12,
    padding: "24px 28px",
    marginBottom: 24,
    boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
    position: "relative",
  },
  cardTitle: {
    margin: "0 0 14px",
    fontSize: "1rem",
    fontWeight: 600,
    color: "#1e293b",
  },
  stepLabel: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    marginBottom: 8,
  },
  stepNum: {
    background: "#eff6ff",
    color: "#2563eb",
    fontWeight: 700,
    fontSize: "0.78rem",
    borderRadius: "50%",
    width: 22,
    height: 22,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
  },
  stepText: {
    fontSize: "0.78rem",
    color: "#94a3b8",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  },
  fileRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    flexWrap: "wrap",
  },
  fileLabel: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    cursor: "pointer",
  },
  fileButton: {
    background: "#f1f5f9",
    border: "1px solid #cbd5e1",
    borderRadius: 6,
    padding: "7px 14px",
    fontSize: "0.88rem",
    color: "#334155",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  fileName: {
    fontSize: "0.86rem",
    color: "#64748b",
    maxWidth: 240,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  btn: {
    background: "#2563eb",
    color: "white",
    border: "none",
    padding: "8px 20px",
    borderRadius: 7,
    cursor: "pointer",
    fontSize: "0.92rem",
    fontWeight: 600,
    transition: "background 0.15s",
  },
  status: {
    fontSize: "0.84rem",
    margin: "10px 0 0",
  },
  pre: {
    background: "#f1f5f9",
    padding: 16,
    borderRadius: 8,
    overflowX: "auto",
    fontSize: "0.78rem",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    marginTop: 14,
    border: "1px solid #e2e8f0",
  },
  hint: {
    fontSize: "0.88rem",
    color: "#64748b",
    margin: "0 0 14px",
  },
  insightsBox: {
    background: "#f1f5f9",
    border: "1px solid #e2e8f0",
    padding: 16,
    borderRadius: 8,
    fontSize: "0.88rem",
    lineHeight: 1.7,
    marginTop: 14,
    color: "#1e293b",
  },
};