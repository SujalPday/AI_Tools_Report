# 🤖 AI Tools Market Analysis Report (2022–2025)

An end-to-end data analysis project examining the adoption, demand, and performance of AI tools across the global developer and enterprise ecosystem — from raw public data to structured insights and interactive dashboards.

---

## 📈 Project Overview

The AI tools landscape has shifted dramatically since 2022. This project answers four specific questions using real, publicly available data:

1. Which AI tools are developers actually using — and how has this changed year on year?
2. Which tools are generating the highest and fastest-growing search demand?
3. How is AI demand reflected in the global job market and research output?
4. What does startup formation data reveal about investor confidence in AI?

---

## 📊 Data Sources

| Source | Dataset | Volume |
|---|---|---|
| Stack Overflow Developer Survey | AI tool usage % by year (2022–2025) | 52 rows |
| Google Trends | Weekly search interest for 10 AI tools | 480 rows |
| Our World in Data | AI publications, job share, company formation by country | 1,675 rows |

All data is publicly available. No paywalled or proprietary sources were used.

---

## ⛓️ Tech Stack & Pipeline

```
Raw CSV Downloads
      ↓
Python (pandas, NumPy)     ← Data cleaning, EDA, statistical analysis
      ↓
MySQL                      ← 9-table relational database (ai_tools_report)
      ↓
Tableau                    ← 5 interactive dashboards
```

**Python libraries used:** pandas · NumPy · matplotlib · statsmodels  
**SQL features used:** CTEs · window functions · joins · aggregations  
**Statistical methods:** Mean, median, std deviation · CAGR · YoY growth · time-series decomposition

---

## 📋 Key Findings

### 🟠 Developer Adoption (Stack Overflow)

| Tool | 2023 | 2024 | 2025 |
|---|---|---|---|
| ChatGPT / OpenAI GPT | — | 85.31% | 82.45% |
| GitHub Copilot | 85.23% | 42.81% | — |
| Anthropic Claude | — | 8.46% | 43.38% |
| Google Gemini | — | 24.87% | 35.77% |

> Claude showed the sharpest YoY growth of any tool — from 8.46% to 43.38% between 2024 and 2025.

### 🟡 Search Demand (Google Trends)

| Tool | Mean Score | Growth | Trend |
|---|---|---|---|
| Cursor | 24.27 | +158.82% | 📈 Rising |
| Claude | 1.23 | +133.33% | 📈 Rising |
| ChatGPT | 30.24 | — | 📈 Rising |
| Grammarly | 44.05 | -51.28% | 📉 Falling |

> Cursor is the fastest-growing tool by search interest, overtaking established players in developer search demand.

### 🔴 Global AI Job Market (Our World in Data)

- AI job share grew from **0.29% (2014) → 2.09% (2025)** — a 620% increase
- Singapore leads at **4.69%**, nearly double the US at **2.56%**
- Newly founded AI companies nearly **doubled in 2025** (6,252 vs 3,657 in 2024)

---

## ⚙️ Project Structure

```
AI-Tools-Market-Analysis-Report-2022-2025/
│
├── data/
│   ├── raw/                  # Original CSV downloads
│   └── cleaned/              # Processed datasets
│
├── notebooks/
│   ├── 01_cleaning.ipynb     # Data cleaning and standardisation
│   ├── 02_eda.ipynb          # Exploratory data analysis
│   └── 03_forecasting.ipynb  # Time-series analysis
│
├── sql/
│   └── schema.sql            # Database schema (ai_tools_report)
│
├── dashboards/               # Tableau workbook files
│
└── report/
    └── AI_Tools_Market_Report_2022_2025.docx
```

---

## 🧱 Limitations

- Stack Overflow changed its AI survey column structure each year — direct YoY comparisons are approximate
- Google Trends uses a relative 0–100 scale, not absolute user counts
- Our World in Data company formation figures for 2025 are estimated from a partial country sample
- GitHub Copilot's zero Trends score is a measurement artefact — it is accessed in-editor, not searched

---

## 📧 About

Built by **Sujal Pandey** — BBA Graduate, Business Analytics  
📧 [sujallpandeyy71@gmail.com] · 🔗 [LinkedIn](https://www.linkedin.com/in/sujal-pandey-820901268/)
