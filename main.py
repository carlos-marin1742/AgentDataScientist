import pandas as pd
from langchain_community.llms import Ollama
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException, status
import json
from starlette.responses import HTMLResponse
import io

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Data Scientist</title>
</head>
<body>
    <h1>Agent Data Scientist</h1>
    <h3>Upload a CSV file and let local AI generate AI EDA code and statistical insights</h3>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".csv">
        <button type="submit">Upload</button>
    </form>

</body>
</html>
"""

app = FastAPI()
@app.get("/", response_class=HTMLResponse)
async def read_root():
     return html_template

@app.post("/upload")
async def upload_csv(file: UploadFile = File(None)):
     """Accepts a CSV file, processes it, and returns AI-generated EDA code and insights."""
     #validating the file type
     if not file.filename.endswith('.csv'):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload a CSV file.")
     #reading the file content
     content = await file.read()
     df = pd.read_csv(io.BytesIO(content))
     #Equivalent of streamlit's st.dataframe(df.head())
     preview = df.head().to_dict(orient="records")
     schema_info = {
          "filename": file.filename,
          "preview": preview,
          "dtypes": df.dtypes.astype(str).to_dict(),
          "missing values": df.isnull().sum().to_dict(),
          "columns": df.columns.tolist(),
          "shape": df.shape}
     return{"raw data preview": schema_info}

class AnalysisRequest(BaseModel):
     schema_info: dict
llm = Ollama(model = "mistral")
@app.post("/generate-analysis")
async def generate_analysis(request: AnalysisRequest):
     prompt = f"""
You are an expert data scientist and Python engineer performing exploratory data analysis (EDA).

DATASET METADATA:
{request.schema_info}

TASK:
Write clean, well-commented, executable Python code that performs a comprehensive EDA. Structure the code in clearly labeled sections.

REQUIREMENTS:

1. SETUP & DATA VALIDATION
   - Import pandas, matplotlib, matplotlib.gridspec, seaborn, numpy, warnings
   - Set seaborn style to 'whitegrid' and a consistent color palette
   - Suppress unnecessary warnings
   - Print dataset shape, dtypes, and first 5 rows

2. SUMMARY STATISTICS
   - Use df.describe(include='all') for full overview
   - Separately report: unique value counts for categoricals, skewness and kurtosis for numericals
   - Print a formatted, readable summary

3. MISSING VALUE ANALYSIS
   - Calculate missing count and percentage per column
   - Create a heatmap (seaborn) showing missing value patterns across rows
   - Add a bar chart showing % missing per column
   - Only generate if missing values exist; print "No missing values detected" otherwise

4. NUMERICAL DISTRIBUTIONS
   - For each numerical column, plot: histogram with KDE overlay, boxplot (to detect outliers)
   - Arrange in a grid layout (2 plots per row)
   - Label axes clearly, include column name as title

5. CATEGORICAL DISTRIBUTIONS
   - For each categorical column (max 10 unique values), plot a horizontal bar chart of value counts
   - Sort bars by frequency, include value labels on bars

6. CORRELATION ANALYSIS
   - Compute correlation matrix for numerical columns
   - Plot an annotated heatmap with a diverging colormap (coolwarm)
   - Mask the upper triangle to reduce redundancy
   - Only generate if 2+ numerical columns exist

7. OUTLIER SUMMARY
   - Use IQR method to flag outliers per numerical column
   - Print a summary table: column name, outlier count, % of rows affected

CONSTRAINTS:
- Return ONLY executable Python code. No markdown formatting, no triple backticks, no explanations outside of inline comments.
- Assume the dataframe is already loaded as `df`.
- Use plt.tight_layout() and plt.show() after each figure block.
- All plots must have titles, axis labels, and figure sizes set explicitly (e.g., figsize=(12, 5)).
- Handle edge cases silently (e.g., skip a plot type if no applicable columns exist).
"""
     try: 
         generated_code = llm(prompt)
         return {
                "generated_code": generated_code
         }
     except Exception as e:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating analysis: {str(e)}")