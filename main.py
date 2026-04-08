import code
import io
import json
import os
from dotenv import load_dotenv
import re
from starlette.staticfiles import StaticFiles
import uvicorn
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq
from pydantic import BaseModel
from starlette.responses import FileResponse
from fastapi.responses import JSONResponse
import base64
import contextlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


# ── App & LLM Setup ───────────────────────────────────────────────────────────
app = FastAPI()
# --- Instantiate LLM ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=api_key,
    temperature=0)
# ── CORS SET UP AND allowing react server ────────────────────────────────────
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ── Pydantic Models ───────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    schema_info: dict


class InsightsRequest(BaseModel):
    preview: list

class RunRequest(BaseModel):
    code: str
    preview: list


# ── Routes ────────────────────────────────────────────────────────────────────

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

        # Convert NaN → None so JSON serialization doesn't choke
    preview = json.loads(df.head().to_json(orient="records"))
    missing_values = json.loads(df.isnull().sum().to_json())

    schema_info = {
        "filename": file.filename,
        "preview": preview,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": missing_values,
        "columns": df.columns.tolist(),
        "shape": list(df.shape),
    }

    return JSONResponse(content={"raw_data_preview": schema_info})


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
        generated_code = llm.invoke(prompt).content
            # Strip markdown fences
        if generated_code.startswith("```"):
            generated_code = re.sub(r"^```(?:python)?\n?", "", generated_code)
            generated_code = re.sub(r"\n?```$", "", generated_code)
        generated_code = generated_code.strip()

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

        insights = llm.invoke(insight_prompt).content
        return {
            "insights": insights,
            "summary_stats": json.loads(df.describe(include="all").to_json()),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating insights: {str(e)}",
        )

@app.post("/run-analysis")
async def run_analysis(request: RunRequest):
    try:
        df = pd.DataFrame(request.preview)
        plots = []
        console_output = io.StringIO()

        # Strip markdown fences if LLM included them
        code = request.code
        if code.startswith("```"):
            code = re.sub(r"^```(?:python)?\n?", "", code)
            code = re.sub(r"\n?```$", "", code)
        code = code.strip()

        #Temp code block remove after fixing
        print("=== FIRST 200 CHARS OF CODE ===")
        print(repr(code[:200]))
        print("================================")

        def capture_show():
            fig = plt.gcf()
            if fig.get_axes():  # only save if figure has actual content
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
                buf.seek(0)
                plots.append(base64.b64encode(buf.read()).decode("utf-8"))
            plt.clf()
            plt.close("all")

        original_show = plt.show
        plt.show = capture_show

        try:
            with contextlib.redirect_stdout(console_output):
                exec(request.code, {
                    "df": df,
                    "plt": plt,
                    "pd": pd,
                    "__builtins__": __builtins__
                })
        except Exception as exec_error:
            return JSONResponse(content={
                "plots": plots,
                "console": console_output.getvalue(),
                "exec_error": str(exec_error)
            })
        finally:
            plt.show = original_show
            plt.close("all")

        return JSONResponse(content={
            "plots": plots,
            "console": console_output.getvalue(),
            "exec_error": None
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running analysis: {str(e)}"
        )


app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    return FileResponse("dist/index.html")
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0", port=int(os.environ.get("PORT", 8000)))