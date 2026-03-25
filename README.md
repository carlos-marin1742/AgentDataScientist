# 🤖 Agent Data Scientist

> **AI-powered exploratory data analysis — upload a CSV, get production-ready EDA code and strategic insights in seconds.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agentdatascientist.streamlit.app/)

🎥 **Demo:** [Watch on YouTube](https://youtu.be/8WTSbu8Z5Vw)  
🚀 **Live App:** [agentdatascientist.streamlit.app](https://agentdatascientist.streamlit.app/)

---

## 📌 Overview

**Agent Data Scientist** is an AI agent that acts as your personal data science assistant. Upload any CSV file and it will:

1. **Generate executable EDA Python code** — structured, commented, and ready to run
2. **Produce a strategic insights report** — statistical patterns, data quality issues, modeling recommendations, and quick wins
3. **Render visualizations inline** — histograms, boxplots, correlation heatmaps, categorical distributions, and more

Powered by **LLaMA 3.3 70B** via the Groq API and built with **LangChain** + **Streamlit**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📂 CSV Upload | Upload any tabular dataset via the sidebar |
| 🧠 EDA Code Generation | LLM writes clean, section-structured Python EDA code |
| 📊 Inline Visualizations | Run the generated code and render plots directly in the app |
| 📝 Insights Report | Strategic analysis report with modeling recommendations |
| ⚡ Groq-Powered | Ultra-fast inference via Groq's LPU hardware |
| 🔁 Session State | Generated code and insights persist across UI interactions |

---

## 🛠️ Tech Stack

- **Frontend / UI:** Streamlit
- **LLM Inference:** [Groq API](https://console.groq.com/) — `llama-3.3-70b-versatile`
- **LLM Orchestration:** LangChain (`langchain-groq`)
- **Data Processing:** Pandas, NumPy
- **Visualization:** Matplotlib, Seaborn
- **Deployment:** [Streamlit Community Cloud](https://streamlit.io/cloud)

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/agent-data-scientist.git
cd agent-data-scientist
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Your API Key

**For local development**, create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Then update `app.py` to use `dotenv` (the commented-out lines at the top of the file):

```python
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
```

**For Streamlit Cloud deployment**, add your key via the Secrets Manager:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "your_groq_api_key_here"
```

### 4. Run the App

```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## 📋 How It Works

```
User uploads CSV
       │
       ▼
Schema extracted (shape, dtypes, missing values, preview)
       │
       ▼
┌──────────────────────────────────────────┐
│         LLM Agent — Step 1               │
│   Generate EDA Python Code               │
│   (7 structured sections, executable)    │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│         LLM Agent — Step 2               │
│   Generate Strategic Insights Report     │
│   (7-section analysis, fully quantified) │
└──────────────────────────────────────────┘
       │
       ▼
User runs code → Plots render inline via st.pyplot()
```

---

## 📊 Generated EDA Code Sections

The agent produces well-structured code covering:

1. **Setup & Data Validation** — imports, style config, shape/dtype summary
2. **Summary Statistics** — `describe(include='all')`, skewness, kurtosis, unique counts
3. **Missing Value Analysis** — heatmap + bar chart of missingness per column
4. **Numerical Distributions** — histograms with KDE overlay + boxplots per column
5. **Categorical Distributions** — sorted horizontal bar charts with value labels
6. **Correlation Analysis** — annotated heatmap with upper triangle masked
7. **Outlier Summary** — IQR-based outlier count and % affected per column

---

## 📝 Insights Report Sections

The agent's strategic report covers:

1. **Dataset Overview** — scope, red flags, modeling readiness
2. **Key Statistical Patterns** — notable distributions, skewness flags, class imbalance
3. **Data Quality Issues** — structured format: Issue / Affected Columns / Severity / Recommended Action
4. **Correlations & Relationships** — strong correlations, multicollinearity risks, redundant features
5. **Target Variable Analysis** — distribution, imbalance, suggested transformations (if applicable)
6. **Modeling Recommendations** — feature engineering, preprocessing pipeline, algorithm fit, validation strategy
7. **Quick Wins** — top 3–5 high-impact actions ranked by effort vs. impact

---

## 📁 Project Structure

```
agent-data-scientist/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── secrets.toml        # API key (Streamlit Cloud, not committed)
├── .env                    # API key (local dev, not committed)
└── README.md
```

---

## ⚙️ Requirements

```txt
streamlit
langchain-groq
langchain
pandas
matplotlib
seaborn
numpy
python-dotenv
sympy
```

---

## 🔐 Security Notes

- Never commit your `.env` file or `secrets.toml` to version control
- Add both to `.gitignore`:

```
.env
.streamlit/secrets.toml
```

---

## 🧩 Future Improvements

- [ ] Support for Excel (`.xlsx`) and JSON file uploads
- [ ] Export insights report as PDF or Word document
- [ ] Follow-up Q&A chat with the agent about the dataset
- [ ] Automatic target column detection for supervised learning context
- [ ] Support for additional LLM providers (Gemini, OpenAI)

---

## 👨‍💻 Author

**Carlos** — Full-Stack Developer & AI/ML Engineer  
Clinical research background informing health tech AI applications.

- Portfolio: [GitHub](https://github.com/carlos-marin1742)
- LinkedIn: [linkedin.com/in/your-profile](https://www.linkedin.com/in/carlos-marin-90482b13b/)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).