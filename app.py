import streamlit as st
from sympy import re
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.pyplot as plt
import contextlib
import io
import re

# --- Instantiate LLM ---
#load_dotenv()
#api_key = os.getenv("GROQ_API_KEY")
api_key = st.secrets["GROQ_API_KEY"]
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=api_key,
    temperature=0
)

# --- Page Config ---
st.set_page_config(page_title="Agent Data Scientist", layout="wide")
st.title("Agent Data Scientist")
st.markdown("Upload a CSV file and let local AI generate EDA code and statistical insights.")

# --- Sidebar ---
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# --- Main Logic ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.write("Data Preview:")
    st.dataframe(df.head())

    schema_info = {
        "filename": uploaded_file.name,
        "preview": df.head().to_dict(orient="records"),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "columns": df.columns.tolist(),
        "shape": df.shape,
    }

    if st.button("Generate Analysis Code & Insights"):
        # --- Step 1: Generate EDA Code ---
        with st.spinner("Generating EDA code..."):
            prompt = f"""
You are an expert data scientist and Python engineer performing exploratory data analysis (EDA).

DATASET METADATA:
{schema_info}

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
- Assume the dataframe is already loaded as df.
- Use plt.tight_layout() and plt.show() after each figure block.
- All plots must have explicit titles, axis labels, and figsize (e.g., figsize=(12, 5)).
- Handle edge cases silently (e.g., skip a plot type if no applicable columns exist).
"""
            generated_code = llm.invoke(prompt)
            code = generated_code.content
            # Strip markdown code fences if the LLM included them
            if code.startswith("```"):
                code = re.sub(r"^```(?:python)?\n?", "", code)
                code = re.sub(r"\n?```$", "", code)
            code = code.strip()
            st.session_state["generated_code"] = code
            

        st.subheader("Generated EDA Code:")
        st.code(st.session_state["generated_code"], language="python")

        # --- Step 2: Generate Insights ---
        with st.spinner("Analyzing statistics and generating insights..."):
            analysis_summary = df.describe(include='all').to_string()
            prompt_insights = f"""
You are a senior data scientist and strategic analytics advisor with deep expertise in
exploratory data analysis, statistical inference, and machine learning preparation.

ANALYSIS SUMMARY:
{analysis_summary}

TASK:
Analyze the provided EDA results and deliver a structured, actionable insights report.
Write for a technical audience (data scientists, ML engineers) while ensuring findings
are clear enough for product or business stakeholders to understand the implications.

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

CONSTRAINTS:
- Be specific: reference actual column names and statistics, never give generic advice
- Quantify claims wherever possible (e.g., "32% missing" not "many missing values")
- If data is insufficient to assess a section, explicitly state why rather than speculating
- Prioritize actionability: every observation should connect to a decision or next step
"""
            insights = llm.invoke(prompt_insights)
            st.session_state["insights"] = insights.content

        st.subheader("Generated Insights Report:")
        st.markdown(st.session_state["insights"])

    # --- Step 3: Run Visualizations (persists across reruns via session_state) ---
    if "generated_code" in st.session_state:
        st.divider()
        if st.checkbox("▶ Run EDA Code & Show Visualizations"):
            original_show = plt.show

            def streamlit_show():
                st.pyplot(plt.gcf())
                plt.clf()

            plt.show = streamlit_show
            exec_output = io.StringIO()

            try:
                with contextlib.redirect_stdout(exec_output):
                    exec(st.session_state["generated_code"], {"df": df})
            except Exception as e:
                st.error(f"Error running generated code: {e}")
            finally:
                plt.show = original_show

            printed_output = exec_output.getvalue()
            if printed_output:
                st.subheader("Console Output:")
                st.text(printed_output)