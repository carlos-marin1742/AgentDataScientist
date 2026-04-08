# 🤖 Agent Data Scientist

A full-stack AI-powered Exploratory Data Analysis (EDA) tool. Upload any CSV and get instant statistical insights, auto-generated EDA code, and live data visualizations — all powered by a LangChain + Groq LLM backend.

**Live Demo:** [agentdatascientist.onrender.com](https://agentdatascientist.onrender.com)

---

## Features

- **CSV Upload & Preview** — Upload any CSV file and instantly see shape, column types, and missing value counts
- **AI Insights Report** — Structured 7-section analytics report covering statistical patterns, data quality issues, correlation analysis, and modeling recommendations
- **Auto-Generated EDA Code** — Production-ready Python EDA code generated from your dataset's schema
- **Live Visualizations** — Execute the generated code server-side and render charts (distributions, correlation heatmaps, outlier boxplots, and more) directly in the browser

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, react-markdown |
| Backend | FastAPI, Uvicorn |
| AI / LLM | LangChain, Groq (`llama-3.3-70b-versatile`) |
| Data | Pandas, Matplotlib, Seaborn, NumPy |
| Deployment | Render |

---

## Project Structure

```
AgentDataScientist/
├── main.py               # FastAPI backend — all routes and LLM logic
├── requirements.txt
├── render.yaml
├── .env                  # GROQ_API_KEY (not committed)
└── client/               # React frontend
    ├── src/
    │   └── App.jsx
    ├── dist/             # Production build served by FastAPI
    └── package.json
```

---

## How It Works

The app runs as a single service on Render — FastAPI serves both the API and the React frontend from the `client/dist/` build.

**Step 1 — Upload CSV**
The `/upload` endpoint reads the file with pandas, extracts schema metadata (shape, dtypes, missing values, preview rows), and returns it as JSON. NaN values are sanitized via pandas' own JSON serializer before transmission.

**Step 2 — Generate Insights**
The `/generate-insights` endpoint passes a `df.describe()` summary to `llama-3.3-70b-versatile` via LangChain-Groq with a structured prompt that produces a 7-section analytics report covering dataset overview, statistical patterns, data quality issues, correlations, target variable analysis, modeling recommendations, and quick wins.

**Step 3 — EDA Visualizations**
The `/generate-analysis` endpoint generates executable Python EDA code from the dataset schema. The `/run-analysis` endpoint then executes that code server-side using `exec()`, intercepts each `plt.show()` call, captures the figure as a base64-encoded PNG, and returns the images to the React frontend for inline rendering.

---

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Groq API key](https://console.groq.com)

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/carlos-marin1742/AgentDataScientist.git
cd AgentDataScientist

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Start the backend
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd client
npm install
npm run dev       # Development server on localhost:3000
```

Or build for production (served by FastAPI):

```bash
cd client
npm run build     # Outputs to client/dist/
```

Then visit `http://localhost:8000` to run the full app through FastAPI.

---

## API Routes

| Method | Route | Description |
|---|---|---|
| `POST` | `/upload` | Upload CSV, returns schema metadata |
| `POST` | `/generate-insights` | Generate AI insights report from preview data |
| `POST` | `/generate-analysis` | Generate EDA Python code from schema |
| `POST` | `/run-analysis` | Execute generated code, return base64 plot images |

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key — get one at [console.groq.com](https://console.groq.com) |

---

## Deployment

This project is configured for one-click deployment on [Render](https://render.com) via `render.yaml`.

The build process installs Python dependencies and starts Uvicorn. The React app must be built locally and committed to the repo (`client/dist/`) so FastAPI can serve it as static files.

---

## Author

**Carlos Marin** — Full-Stack AI Developer
[GitHub](https://github.com/carlos-marin1742)