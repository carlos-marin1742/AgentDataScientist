# 🤖 Agent Data Scientist

An AI-powered data science agent that analyzes uploaded CSV datasets, generates executable EDA Python code, and produces structured analytical insights reports — all driven by a large language model.

---

## Demo

> Upload a CSV → Generate EDA Code → Run Visualizations → Read Insights Report

**Live Demo:** [https://agentdatascientist.streamlit.app/](https://agentdatascientist.streamlit.app/) 
---

## Features

- **EDA Code Generation** — Dynamically generates clean, well-commented, executable Python code structured across 7 analysis sections: setup, summary statistics, missing value analysis, numerical distributions, categorical distributions, correlation analysis, and outlier detection
- **Insights Report** — Produces a structured analytical report covering dataset overview, statistical patterns, data quality issues, correlations, target variable analysis, modeling recommendations, and quick wins
- **In-App Visualization** — Runs generated EDA code directly in the browser and renders all matplotlib/seaborn plots inline
- **Modular Prompt System** — Prompts are versioned and parameterized with optional section flags, enabling reproducible LLM outputs
- **Console Output Capture** — Captures and displays all print statements from the generated EDA code alongside visualizations

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Inference | Groq API — `llama-3.3-70b-versatile` |
| LLM Orchestration | LangChain |
| Data Processing | Pandas |
| Visualization | Matplotlib, Seaborn |
| Frontend | Streamlit |
| Backend API | FastAPI |
| Secret Management | Streamlit Secrets / `.env` |

---

## Project Structure

```
agent-data-scientist/
├── streamlit_app.py        # Streamlit UI + LLM orchestration
├── main.py                 # FastAPI backend (REST API version)
├── prompts/
│   ├── __init__.py         # Central prompt registry
│   ├── eda_prompt.py       # EDA code generation prompt
│   └── insights_prompt.py  # Insights report prompt
├── requirements.txt
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- A [Groq API key](https://console.groq.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/carlos-marin1742/AgentDataScientist
cd agent-data-scientist

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

```bash
# Copy the example env file
cp .env.example .env

# Add your Groq API key
GROQ_API_KEY=your_key_here
```

### Run Streamlit App

```bash
streamlit run streamlit_app.py
```

### Run FastAPI Backend

```bash
uvicorn main:app --reload
# API docs available at http://localhost:8000/docs
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload CSV, returns schema and data preview |
| `POST` | `/generate-analysis` | Generate EDA Python code from schema metadata |
| `POST` | `/generate-insights` | Generate insights report from dataset preview |

---

## EDA Sections Generated

The agent generates code covering all 7 sections:

1. **Setup & Data Validation** — imports, style config, shape/dtype/preview print
2. **Summary Statistics** — `describe()`, skewness, kurtosis, unique value counts
3. **Missing Value Analysis** — heatmap + bar chart (skipped if no missing values)
4. **Numerical Distributions** — histogram + KDE + boxplot per numerical column
5. **Categorical Distributions** — horizontal bar charts with value labels
6. **Correlation Analysis** — annotated heatmap with upper triangle masked
7. **Outlier Summary** — IQR method, count and % per column

---

## Insights Report Structure

The insights report covers 7 sections:

1. **Dataset Overview** — scope, red flags, modeling readiness
2. **Key Statistical Patterns** — distributions, skewness, kurtosis, class imbalance
3. **Data Quality Issues** — severity-tagged issues with recommended actions
4. **Correlations & Relationships** — strong correlations, multicollinearity risks
5. **Target Variable Analysis** — distribution, imbalance, transformation suggestions
6. **Modeling Recommendations** — feature engineering, preprocessing pipeline, algorithm fit, validation strategy
7. **Quick Wins** — 3–5 prioritized actions ranked by effort vs. impact

---

## Requirements

```
streamlit
langchain-groq
langchain-community
pandas
matplotlib
seaborn
numpy
python-dotenv
fastapi
uvicorn
python-multipart
pydantic
```

---

## License

MIT