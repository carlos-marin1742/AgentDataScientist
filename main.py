import io
import json

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from langchain_community.llms import Ollama
from pydantic import BaseModel
from starlette.responses import HTMLResponse

# ── HTML Template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Data Scientist</title>
    <style>
        body { font-family: sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; background: #f9f9f9; }
        h1 { color: #222; }
        h3 { color: #555; font-weight: normal; }
        section { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 24px; margin-bottom: 24px; }
        section h2 { margin-top: 0; font-size: 1.1rem; color: #333; }
        button { background: #2563eb; color: white; border: none; padding: 8px 18px; border-radius: 5px; cursor: pointer; font-size: 0.95rem; }
        button:hover { background: #1d4ed8; }
        button:disabled { background: #93c5fd; cursor: not-allowed; }
        pre { background: #f1f5f9; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 0.82rem; white-space: pre-wrap; word-break: break-word; }
        #insights-output { background: #f1f5f9; padding: 16px; border-radius: 6px; white-space: pre-wrap; font-size: 0.88rem; line-height: 1.6; }
        .status { font-size: 0.85rem; color: #6b7280; margin-top: 8px; }
        .error { color: #dc2626; }
    </style>
</head>
<body>
    <h1>Agent Data Scientist</h1>
    <h3>Upload a CSV file and let local AI generate EDA code and statistical insights</h3>

    <!-- Step 1: Upload CSV -->
    <section>
        <h2>Step 1 - Upload CSV</h2>
        <input type="file" id="csvFile" accept=".csv">
        <button onclick="uploadCSV()" style="margin-left:10px">Upload</button>
        <p class="status" id="upload-status"></p>
        <pre id="upload-result" style="display:none"></pre>
    </section>

    <!-- Step 2: Generate Insights -->
    <section>
        <h2>Step 2 - Generate Insights</h2>
        <p style="font-size:0.9rem; color:#555; margin-top:0">Upload a CSV first, then click below to run the AI insights report.</p>
        <button id="insights-btn" onclick="generateInsights()" disabled>Generate Insights</button>
        <p class="status" id="insights-status"></p>
        <div id="insights-output" style="display:none"></div>
    </section>

    <script>
        let previewData = null;

        async function uploadCSV() {
            const fileInput = document.getElementById("csvFile");
            const statusEl = document.getElementById("upload-status");
            const resultEl = document.getElementById("upload-result");

            if (!fileInput.files.length) {
                statusEl.textContent = "Please select a CSV file first.";
                return;
            }

            statusEl.className = "status";
            statusEl.textContent = "Uploading...";
            const formData = new FormData();
            formData.append("file", fileInput.files[0]);

            try {
                const res = await fetch("/upload", { method: "POST", body: formData });
                const text = await res.text();

                let data;
                try { data = JSON.parse(text); }
                catch { throw new Error("Server returned non-JSON: " + text.slice(0, 200)); }

                if (!res.ok) throw new Error(data.detail || "Upload failed.");

                previewData = data.raw_data_preview.preview;
                resultEl.textContent = JSON.stringify(data, null, 2);
                resultEl.style.display = "block";
                statusEl.textContent = "Uploaded: " + data.raw_data_preview.filename
                    + " - " + data.raw_data_preview.shape[0] + " rows x " + data.raw_data_preview.shape[1] + " cols";
                document.getElementById("insights-btn").disabled = false;
                document.getElementById("insights-status").textContent = "Ready to generate insights.";
            } catch (err) {
                statusEl.className = "status error";
                statusEl.textContent = "Error: " + err.message;
            }
        }

        async function generateInsights() {
            if (!previewData) return;

            const btn = document.getElementById("insights-btn");
            const statusEl = document.getElementById("insights-status");
            const outputEl = document.getElementById("insights-output");

            btn.disabled = true;
            statusEl.className = "status";
            statusEl.textContent = "Generating insights... this may take a moment.";
            outputEl.style.display = "none";

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

                outputEl.textContent = data.insights;
                outputEl.style.display = "block";
                statusEl.textContent = "Insights generated.";
            } catch (err) {
                statusEl.className = "status error";
                statusEl.textContent = "Error: " + err.message;
            } finally {
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

# ── App & LLM Setup ───────────────────────────────────────────────────────────

app = FastAPI()
llm = Ollama(model="mistral")


# ── Pydantic Models ───────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    schema_info: dict


class InsightsRequest(BaseModel):
    preview: list


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_TEMPLATE


@app.post("/upload")
async def upload_csv(file: UploadFile = File(None)):
    """Accept a CSV file, process it, and return a schema preview."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a CSV file.",
        )

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    schema_info = {
        "filename": file.filename,
        "preview": df.head().to_dict(orient="records"),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "columns": df.columns.tolist(),
        "shape": df.shape,
    }

    return {"raw_data_preview": schema_info}


@app.post("/generate-analysis")
async def generate_analysis(request: AnalysisRequest):
    """Generate executable EDA Python code from dataset metadata."""
    prompt = f"""
You are an expert data scientist and Python engineer performing exploratory data analysis (EDA).

DATASET METADATA:
{request.schema_info}

TASK:
Write clean, well-commented, executable Python code that performs a comprehensive EDA.
Structure the code in clearly labeled sections.

REQUIREMENTS:

1. SETUP & DATA VALIDATION
   - Import pandas, matplotlib, matplotlib.gridspec, seaborn, numpy, warnings
   - Set seaborn style to 'whitegrid' and a consistent color palette
   - Suppress unnecessary warnings
   - Print dataset shape, dtypes, and first 5 rows

2. SUMMARY STATISTICS
   - Use df.describe(include='all') for a full overview
   - Separately report: unique value counts for categoricals, skewness and kurtosis for numericals
   - Print a formatted, readable summary

3. MISSING VALUE ANALYSIS
   - Calculate missing count and percentage per column
   - Create a seaborn heatmap showing missing value patterns across rows
   - Add a bar chart showing % missing per column
   - Skip if no missing values exist; print "No missing values detected" instead

4. NUMERICAL DISTRIBUTIONS
   - For each numerical column plot: histogram with KDE overlay, and a boxplot for outlier detection
   - Arrange in a grid layout (2 plots per row)
   - Label axes clearly; use column name as the title

5. CATEGORICAL DISTRIBUTIONS
   - For each categorical column (max 10 unique values), plot a horizontal bar chart of value counts
   - Sort bars by frequency and include value labels on bars

6. CORRELATION ANALYSIS
   - Compute the correlation matrix for numerical columns
   - Plot an annotated heatmap with a diverging colormap (coolwarm)
   - Mask the upper triangle to reduce redundancy
   - Skip if fewer than 2 numerical columns exist

7. OUTLIER SUMMARY
   - Use the IQR method to flag outliers per numerical column
   - Print a summary table: column name, outlier count, % of rows affected

CONSTRAINTS:
- Return ONLY executable Python code - no markdown, no triple backticks, no prose outside inline comments.
- Assume the dataframe is already loaded as `df`.
- Use plt.tight_layout() and plt.show() after each figure block.
- All plots must have explicit titles, axis labels, and figsize (e.g., figsize=(12, 5)).
- Handle edge cases silently (e.g., skip a plot type if no applicable columns exist).
"""

    try:
        generated_code = llm.invoke(prompt)
        return {"generated_code": generated_code}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating analysis: {str(e)}",
        )


@app.post("/generate-insights")
async def generate_insights(request: InsightsRequest):
    """Generate a structured insights report from a dataset preview."""
    try:
        df = pd.DataFrame(request.preview)
        analysis_summary = df.describe(include="all").to_string()

        insight_prompt = f"""
You are a senior data scientist and strategic analytics advisor with deep expertise in
exploratory data analysis, statistical inference, and machine learning preparation.

ANALYSIS SUMMARY:
{analysis_summary}

TASK:
Analyze the provided EDA results and deliver a structured, actionable insights report.
Write for a technical audience (data scientists, ML engineers) while ensuring findings
are clear enough for product or business stakeholders to understand the implications.

---

REPORT STRUCTURE:

1. DATASET OVERVIEW
- Summarize scope: row/column count and data type breakdown
- Assess whether the dataset is suitable for modeling as-is
- Flag any immediate red flags before deep analysis

2. KEY STATISTICAL PATTERNS
- Identify the most notable distributions (normal, skewed, bimodal, uniform)
- Flag columns with high skewness (|skew| > 1) or excess kurtosis
- Highlight surprising descriptive statistics (unexpected min/max, zero variance, etc.)
- Note dominant categories in categorical columns and any class imbalance

3. DATA QUALITY ISSUES
For each issue found, use this format:
Issue: [description]
Affected Column(s): [column names]
Severity: [Low / Medium / High]
Recommended Action: [specific fix or investigation step]
Cover: missing values, outliers, near-constant columns, potential duplicates,
dtype mismatches, and impossible values (e.g., negative age).

4. CORRELATIONS AND RELATIONSHIPS
- Summarize the strongest positive and negative correlations (|r| > 0.5)
- Flag multicollinearity risks for regression-type models (|r| > 0.85)
- Identify potential feature interaction candidates
- Note any features that appear redundant or derivable from others

5. TARGET VARIABLE ANALYSIS (if applicable)
- If a likely target column is detectable, comment on its distribution
- Flag class imbalance (classification) or heavy skew (regression)
- Suggest transformations if needed (e.g., log-transform for right-skewed targets)

6. MODELING RECOMMENDATIONS
Feature Engineering:
- Suggest transformations (log, sqrt, binning, encoding strategies)
- Recommend interaction terms or ratio features worth exploring
Preprocessing Pipeline:
- Imputation strategy per column (mean / median / mode / model-based)
- Scaling recommendation (StandardScaler vs. MinMaxScaler vs. RobustScaler)
- Encoding strategy for categoricals (OHE, target encoding, ordinal)
Algorithm Fit:
- Suggest 2-3 suitable model families based on data characteristics
- Note data properties that would hurt specific algorithms (e.g., outliers hurt linear models)
Validation Strategy:
- Recommend a train/test split or cross-validation strategy
- Flag any data leakage risks spotted in the features

7. QUICK WINS
- List 3-5 immediate, high-impact actions ranked by effort vs. impact
- Format as: [Action] -> [Expected Benefit]

---

CONSTRAINTS:
- Be specific: reference actual column names and statistics, never give generic advice
- Quantify claims wherever possible (e.g., "32% missing" not "many missing values")
- If data is insufficient to assess a section, explicitly state why rather than speculating
- Prioritize actionability: every observation should connect to a decision or next step
"""

        insights = llm.invoke(insight_prompt)
        return {
            "insights": insights,
            "summary_stats": json.loads(df.describe(include="all").to_json()),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating insights: {str(e)}",
        )