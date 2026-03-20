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
raw_data_previewHTML = """
<h2>Raw Data Preview</h2>

"""
def statistical_insights(df):
    header = df.head()
    description = df.describe()
    dtypes = df.dtypes.astype(str).to_dict()
    columns = df.columns.tolist()
    shape = df.shape
    return header, description, dtypes, columns, shape

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
@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
     return {"message": "Analysis complete"}