import pandas as pd
from langchain_community.llms import Ollama
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from starlette.templating import Jinja2Templates
from starlette.responses import HTMLResponse
import io
import csv

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
async def upload_csv(file: UploadFile = File(...)):
     """Accepts a CSV file, processes it, and returns AI-generated EDA code and insights."""
     #validating the file type
     if not file.filename.endswith('.csv'):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload a CSV file.")
     #reading the file content
     content = await file.read()
     #loading the content into a pandas DataFrame
    sio = io.StringIO(content.decode('utf-8'))
    uploaded_file = pd.read_csv(sio)
     #generating EDA code and insights using the local AI model
     if uploaded_file is not None:


     await file.close()
    return JSONResponse(content={"message": "File uploaded and processed successfully. AI-generated EDA code and insights will be returned here."})



