import pandas as pd
import numpy as np
import os

#  Load all 4 survey files 
BASE_DIR = r"[Paste directory here]"

files = {
    2022: "survey_2022.csv",
    2023: "survey_2023.csv",
    2024: "survey_2024.csv",
    2025: "survey_2025.csv",
}

surveys = {}

#  Print column names per year 
for year, filename in files.items():
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, low_memory=False)
        surveys[year] = df

#  AI column mapping per year 
# Different years use different column names — we standardise them here

AI_COLUMNS = {
    2022: {
        # No AI columns in 2022 — used as baseline only
    },
    2023: {
        'ai_tool_used'     : 'AIDevHaveWorkedWith',
        'ai_sentiment'     : 'AISent',
        'ai_benefit'       : 'AIBen',
        'ai_accuracy'      : 'AIAcc',
        'ai_currently_use' : 'AIToolCurrently Using',
    },
    2024: {
        'ai_tool_used'     : 'AISearchDevHaveWorkedWith',
        'ai_sentiment'     : 'AISent',
        'ai_benefit'       : 'AIBen',
        'ai_accuracy'      : 'AIAcc',
        'ai_currently_use' : 'AIToolCurrently Using',
        'ai_threat'        : 'AIThreat',
    },
    2025: {
        'ai_tool_used'     : 'AIModelsHaveWorkedWith',
        'ai_sentiment'     : 'AISent',
        'ai_accuracy'      : 'AIAcc',
        'ai_currently_use' : 'AIToolCurrently mostly AI',
        'ai_threat'        : 'AIThreat',
    },
}

#  Extract AI columns + keep year + respondent count 
ai_data = {}

for year, df in surveys.items():
    col_map = AI_COLUMNS.get(year, {})

    if not col_map:
        ai_data[year] = pd.DataFrame()
        continue

    # Only keep columns that exist in this year's dataset
    valid_cols = {std: orig for std, orig in col_map.items() if orig in df.columns}
    missing    = {std: orig for std, orig in col_map.items() if orig not in df.columns}

    df_ai = df[[col for col in valid_cols.values()]].copy()
    df_ai.columns = list(valid_cols.keys())   # rename to standard names
    df_ai['year'] = year

    ai_data[year] = df_ai

#  Step 4: AI Tool Usage Rate per Year 

tool_usage_all_years = []

for year, df_ai in ai_data.items():

    # Skip 2022 — no AI columns
    if df_ai.empty:
        continue

    # Skip years where ai_tool_used column wasn't extracted
    if 'ai_tool_used' not in df_ai.columns:
        print(f"  {year} — No ai_tool_used column, skipping.")
        continue

    total_respondents = df_ai['ai_tool_used'].notna().sum()

    # Each cell looks like: "ChatGPT;GitHub Copilot;Gemini"
    # We split by ; and count each tool individually
    tools_series = (
        df_ai['ai_tool_used']
        .dropna()
        .str.split(';')
        .explode()
        .str.strip()
    )

    tool_counts  = tools_series.value_counts()
    tool_pct     = (tool_counts / total_respondents * 100).round(2)

    df_year = pd.DataFrame({
        'tool_name'        : tool_counts.index,
        'respondent_count' : tool_counts.values,
        'usage_rate_pct'   : tool_pct.values,
        'year'             : year,
        'total_respondents': total_respondents
    }).reset_index(drop=True)

    tool_usage_all_years.append(df_year)

#  Combine all years into one DataFrame 
df_tool_usage = pd.concat(tool_usage_all_years, ignore_index=True)

#  Step 5: NumPy Analysis 

print("\n" + "="*50)
print("  NUMPY ANALYSIS")
print("="*50)

#  1. Stats per year 
for year in sorted(df_tool_usage['year'].unique()):
    df_yr  = df_tool_usage[df_tool_usage['year'] == year]
    arr    = df_yr['usage_rate_pct'].values

    print(f"\n  {year}:")
    print(f"    Tools tracked : {len(arr)}")
    print(f"    Mean usage    : {np.mean(arr):.2f}%")
    print(f"    Median usage  : {np.median(arr):.2f}%")
    print(f"    Std deviation : {np.std(arr):.2f}%")
    print(f"    Top tool      : {df_yr.iloc[0]['tool_name']} ({np.max(arr):.2f}%)")

#  2. Year-over-year growth for tools present in both 
# Compare tools that appear in both 2023 & 2024
print(f"\n{'='*50}")
print("  YEAR-OVER-YEAR GROWTH (2023 → 2024)")
print("="*50)

tools_2023 = df_tool_usage[df_tool_usage['year'] == 2023].set_index('tool_name')['usage_rate_pct']
tools_2024 = df_tool_usage[df_tool_usage['year'] == 2024].set_index('tool_name')['usage_rate_pct']

common_tools_23_24 = tools_2023.index.intersection(tools_2024.index)

yoy_rows = []
for tool in common_tools_23_24:
    pct_23   = tools_2023[tool]
    pct_24   = tools_2024[tool]
    growth   = round(((pct_24 - pct_23) / pct_23) * 100, 2) if pct_23 > 0 else None
    yoy_rows.append({
        'tool_name'  : tool,
        'usage_2023' : pct_23,
        'usage_2024' : pct_24,
        'yoy_growth' : growth
    })

df_yoy = pd.DataFrame(yoy_rows).sort_values('yoy_growth', ascending=False)
print(df_yoy.to_string(index=False))

#    3. Respondent growth year over year 
print(f"\n{'='*50}")
print("  RESPONDENT COUNT GROWTH (survey participation)")
print("="*50)

respondents = {
    year: df_tool_usage[df_tool_usage['year'] == year]['total_respondents'].iloc[0]
    for year in sorted(df_tool_usage['year'].unique())
}

years_arr  = np.array(list(respondents.keys()))
counts_arr = np.array(list(respondents.values()))

for i, year in enumerate(years_arr):
    if i == 0:
        print(f"  {year}: {counts_arr[i]:,} respondents (baseline)")
    else:
        growth = ((counts_arr[i] - counts_arr[i-1]) / counts_arr[i-1]) * 100
        print(f"  {year}: {counts_arr[i]:,} respondents ({growth:+.1f}% vs {years_arr[i-1]})")

#  Step 6: Save CSVs + Generate MySQL file 

#  6A. Save CSVs 
df_tool_usage.to_csv("so_tool_usage.csv", index=False)
print(" Saved: so_tool_usage.csv")

df_yoy.to_csv("so_yoy_growth.csv", index=False)
print(" Saved: so_yoy_growth.csv")

#  6B. Stats summary CSV 
stats_rows = []
for year in sorted(df_tool_usage['year'].unique()):
    df_yr = df_tool_usage[df_tool_usage['year'] == year]
    arr   = df_yr['usage_rate_pct'].values
    stats_rows.append({
        'year'              : year,
        'tools_tracked'     : len(arr),
        'mean_usage_pct'    : round(np.mean(arr), 2),
        'median_usage_pct'  : round(np.median(arr), 2),
        'std_dev'           : round(np.std(arr), 2),
        'top_tool'          : df_yr.iloc[0]['tool_name'],
        'top_tool_usage_pct': round(np.max(arr), 2),
        'total_respondents' : df_yr['total_respondents'].iloc[0]
    })

df_stats = pd.DataFrame(stats_rows)
df_stats.to_csv("so_yearly_stats.csv", index=False)
print(" Saved: so_yearly_stats.csv")

print(f"\n  Stats summary:")
print(df_stats.to_string(index=False))

#  6C. Generate MySQL .sql file 
sql_lines = []

sql_lines.append("-- ============================================")
sql_lines.append("-- AI TOOLS REPORT — Stack Overflow Data")
sql_lines.append("-- Run this in MySQL Workbench")
sql_lines.append("-- ============================================\n")

sql_lines.append("CREATE DATABASE IF NOT EXISTS ai_tools_report;")
sql_lines.append("USE ai_tools_report;\n")

#   Table 1: Tool usage 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS so_tool_usage (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    tool_name          VARCHAR(150),
    respondent_count   INT,
    usage_rate_pct     DECIMAL(5,2),
    year               INT,
    total_respondents  INT
);\n""")

sql_lines.append("INSERT INTO so_tool_usage (tool_name, respondent_count, usage_rate_pct, year, total_respondents) VALUES")
rows = []
for _, row in df_tool_usage.iterrows():
    name = str(row['tool_name']).replace("'", "\\'")
    rows.append(
        f"  ('{name}', {int(row['respondent_count'])}, "
        f"{row['usage_rate_pct']}, {int(row['year'])}, "
        f"{int(row['total_respondents'])})"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Table 2: YoY growth 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS so_yoy_growth (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    tool_name    VARCHAR(150),
    usage_2023   DECIMAL(5,2),
    usage_2024   DECIMAL(5,2),
    yoy_growth   DECIMAL(8,2)
);\n""")

sql_lines.append("INSERT INTO so_yoy_growth (tool_name, usage_2023, usage_2024, yoy_growth) VALUES")
rows = []
for _, row in df_yoy.iterrows():
    name = str(row['tool_name']).replace("'", "\\'")
    rows.append(
        f"  ('{name}', {row['usage_2023']}, "
        f"{row['usage_2024']}, {row['yoy_growth']})"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Table 3: Yearly stats 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS so_yearly_stats (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    year                INT,
    tools_tracked       INT,
    mean_usage_pct      DECIMAL(5,2),
    median_usage_pct    DECIMAL(5,2),
    std_dev             DECIMAL(5,2),
    top_tool            VARCHAR(150),
    top_tool_usage_pct  DECIMAL(5,2),
    total_respondents   INT
);\n""")

sql_lines.append("INSERT INTO so_yearly_stats (year, tools_tracked, mean_usage_pct, median_usage_pct, std_dev, top_tool, top_tool_usage_pct, total_respondents) VALUES")
rows = []
for _, row in df_stats.iterrows():
    top = str(row['top_tool']).replace("'", "\\'")
    rows.append(
        f"  ({int(row['year'])}, {int(row['tools_tracked'])}, "
        f"{row['mean_usage_pct']}, {row['median_usage_pct']}, "
        f"{row['std_dev']}, '{top}', "
        f"{row['top_tool_usage_pct']}, {int(row['total_respondents'])})"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Useful queries 
sql_lines.append("""
-- ============================================
-- USEFUL QUERIES
-- ============================================

-- Top tools per year
SELECT year, tool_name, usage_rate_pct
FROM so_tool_usage
ORDER BY year, usage_rate_pct DESC;

-- Fastest growing tools (2023 → 2024)
SELECT tool_name, usage_2023, usage_2024, yoy_growth
FROM so_yoy_growth
ORDER BY yoy_growth DESC;

-- Yearly summary stats
SELECT year, top_tool, top_tool_usage_pct,
       mean_usage_pct, total_respondents
FROM so_yearly_stats
ORDER BY year;
""")

#  Write file 
with open("so_mysql.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print("\n Saved: so_mysql.sql")
print("  → Open MySQL Workbench → File → Open SQL Script → run it")
