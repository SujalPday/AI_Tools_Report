#  Step 9: Load & Clean Google Trends Data 

import pandas as pd
import numpy as np
import os

os.chdir("[Paste directory here]")

def load_trends_batch(trends):
    # Google Trends CSVs have 2 junk rows at the top — skip them
    df = pd.read_csv(trends, skiprows=2)

    # Rename first column to 'week'
    df.rename(columns={df.columns[0]: 'week'}, inplace=True)

    # Drop empty rows
    df = df.dropna(subset=['week'])

    # Convert week to datetime
    df['week'] = pd.to_datetime(df['week'], errors='coerce')
    df = df.dropna(subset=['week'])

    # Replace '<1' with 0 (Google uses this for very low values)
    for col in df.columns[1:]:
        df[col] = df[col].replace('<1', '0')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

#  Load both batches 
df_b1 = load_trends_batch("trends_batch1.csv")
df_b2 = load_trends_batch("trends_batch2.csv")

print("Batch 1 shape:", df_b1.shape)
print("Batch 2 shape:", df_b2.shape)
print("\nBatch 1 columns:", list(df_b1.columns))
print("Batch 2 columns:", list(df_b2.columns))

print("\nBatch 1 sample:")
print(df_b1.head(3).to_string())
print("\nBatch 2 sample:")
print(df_b2.head(3).to_string())

#  Merge both batches on 'week' 
df_trends = pd.merge(df_b1, df_b2, on='week', how='outer')
df_trends = df_trends.sort_values('week').reset_index(drop=True)

#  Add time columns 
df_trends['year']  = df_trends['week'].dt.year
df_trends['month'] = df_trends['week'].dt.to_period('M').astype(str)

#  Step 10: Clean column names & filter dates 

# Clean tool column names — remove ": (Worldwide)" suffix
df_trends.columns = [
    col.replace(': (Worldwide)', '').strip().title()
    if col not in ['week', 'year', 'month']
    else col
    for col in df_trends.columns
]

print("Cleaned columns:", list(df_trends.columns))

# Filter to 2022 onwards only
df_trends = df_trends[df_trends['year'] >= 2022].reset_index(drop=True)

print(f"\nAfter date filter:")
print(f"  Shape      : {df_trends.shape}")
print(f"  Date range : {df_trends['week'].min().date()} → {df_trends['week'].max().date()}")
print(f"  Total weeks: {len(df_trends)}")

#  Preview cleaned data 
tool_cols = [c for c in df_trends.columns if c not in ['week', 'year', 'month']]

#  Step 11: Fix names & analyse trends 

# Fix capitalisation of specific tool names
df_trends.rename(columns={
    'Chatgpt': 'ChatGPT',
    'Notion Ai': 'Notion AI'
}, inplace=True)

tool_cols = [c for c in df_trends.columns if c not in ['week', 'year', 'month']]
print("Final tool columns:", tool_cols)

#  Monthly average (cleaner for Tableau) 
df_monthly = (
    df_trends
    .groupby('month')[tool_cols]
    .mean()
    .round(2)
    .reset_index()
)
df_monthly['year'] = df_monthly['month'].str[:4].astype(int)

print(f"\nMonthly averages shape: {df_monthly.shape}")

#  NumPy analysis per tool 
print(f"\n{'=' * 60}")
print("  GOOGLE TRENDS — TOOL STATS (2022–2025)")
print(f"{'=' * 60}")

stats_rows = []
for tool in tool_cols:
    arr = df_trends[tool].values

    # Growth: compare average of last 3 months vs first 3 months
    start_avg = np.mean(arr[:3])
    end_avg = np.mean(arr[-3:])
    growth = round(((end_avg - start_avg) / start_avg * 100), 2) if start_avg > 0 else None

    # Peak month
    peak_idx = np.argmax(arr)
    peak_week = df_trends['week'].iloc[peak_idx].strftime('%Y-%m')

    stats_rows.append({
        'tool': tool,
        'mean_score': round(np.mean(arr), 2),
        'max_score': int(np.max(arr)),
        'min_score': int(np.min(arr)),
        'std_dev': round(np.std(arr), 2),
        'peak_month': peak_week,
        'growth_pct': growth,
        'trend': 'Rising' if growth and growth > 0 else 'Falling'
    })

df_trend_stats = pd.DataFrame(stats_rows).sort_values('mean_score', ascending=False)
print(df_trend_stats.to_string(index=False))

#  Year-wise average per tool 
print(f"\n{'=' * 60}")
print("  YEARLY AVERAGE INTEREST PER TOOL")
print(f"{'=' * 60}")

df_yearly_avg = (
    df_trends
    .groupby('year')[tool_cols]
    .mean()
    .round(2)
    .reset_index()
)
print(df_yearly_avg.to_string(index=False))

#  Step 12: Save CSVs + Generate MySQL file 

#  Long format (best for Tableau & MySQL) 
df_long = df_monthly.melt(
    id_vars    = ['month', 'year'],
    value_vars = tool_cols,
    var_name   = 'tool_name',
    value_name = 'interest_score'
)
df_long['month'] = pd.to_datetime(df_long['month'].astype(str) + '-01')
df_long['source'] = 'Google Trends'

#  Save CSVs 
df_trends.to_csv("trends_clean.csv", index=False)
print(" Saved: trends_clean.csv")

df_long.to_csv("trends_long.csv", index=False)
print(" Saved: trends_long.csv       ← use this in Tableau")

df_trend_stats.to_csv("trends_stats.csv", index=False)
print(" Saved: trends_stats.csv")

df_yearly_avg.to_csv("trends_yearly_avg.csv", index=False)
print(" Saved: trends_yearly_avg.csv")

#  Generate MySQL .sql file 
sql_lines = []

sql_lines.append("-- ============================================")
sql_lines.append("-- AI TOOLS REPORT — Google Trends Data")
sql_lines.append("-- Run this in MySQL Workbench")
sql_lines.append("-- ============================================\n")

sql_lines.append("USE ai_tools_report;\n")
sql_lines.append("TRUNCATE TABLE google_trends;")
sql_lines.append("TRUNCATE TABLE trends_tool_stats;")
sql_lines.append("TRUNCATE TABLE trends_yearly_avg;\n")

#  Table 1: Monthly interest (long format) 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS google_trends (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    month          VARCHAR(10),
    year           INT,
    tool_name      VARCHAR(100),
    interest_score DECIMAL(5,2),
    source         VARCHAR(50)
);\n""")

sql_lines.append("INSERT INTO google_trends (month, year, tool_name, interest_score, source) VALUES")
rows = []
for _, row in df_long.iterrows():
    tool = str(row['tool_name']).replace("'", "\\'")
    rows.append(
        f"  ('{row['month']}', {int(row['year'])}, "
        f"'{tool}', {row['interest_score']}, 'Google Trends')"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Table 2: Tool stats summary 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS trends_tool_stats (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    tool        VARCHAR(100),
    mean_score  DECIMAL(5,2),
    max_score   INT,
    min_score   INT,
    std_dev     DECIMAL(5,2),
    peak_month  VARCHAR(10),
    growth_pct  DECIMAL(8,2),
    trend       VARCHAR(10)
);\n""")

sql_lines.append("INSERT INTO trends_tool_stats (tool, mean_score, max_score, min_score, std_dev, peak_month, growth_pct, trend) VALUES")
rows = []
for _, row in df_trend_stats.iterrows():
    tool       = str(row['tool']).replace("'", "\\'")
    growth_val = 'NULL' if pd.isna(row['growth_pct']) else str(row['growth_pct'])
    rows.append(
        f"  ('{tool}', {row['mean_score']}, {row['max_score']}, "
        f"{row['min_score']}, {row['std_dev']}, '{row['peak_month']}', "
        f"{growth_val}, '{row['trend']}')"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Table 3: Yearly average interest 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS trends_yearly_avg (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    year             INT,
    tool_name        VARCHAR(100),
    avg_interest     DECIMAL(5,2)
);\n""")

# Melt yearly avg to long format for MySQL
df_yearly_long = df_yearly_avg.melt(
    id_vars    = ['year'],
    value_vars = tool_cols,
    var_name   = 'tool_name',
    value_name = 'avg_interest'
)

sql_lines.append("INSERT INTO trends_yearly_avg (year, tool_name, avg_interest) VALUES")
rows = []
for _, row in df_yearly_long.iterrows():
    tool = str(row['tool_name']).replace("'", "\\'")
    rows.append(
        f"  ({int(row['year'])}, '{tool}', {row['avg_interest']})"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Useful queries 
sql_lines.append("""
-- ============================================
-- USEFUL QUERIES
-- ============================================

-- Monthly interest for ChatGPT over time
SELECT month, interest_score
FROM google_trends
WHERE tool_name = 'ChatGPT'
ORDER BY month ASC;

-- Peak interest per tool
SELECT tool_name, MAX(interest_score) AS peak_interest
FROM google_trends
GROUP BY tool_name
ORDER BY peak_interest DESC;

-- Rising vs Falling tools
SELECT tool, trend, growth_pct, peak_month
FROM trends_tool_stats
ORDER BY growth_pct DESC;

-- Year wise average per tool
SELECT year, tool_name, avg_interest
FROM trends_yearly_avg
ORDER BY year, avg_interest DESC;
""")

#  Write file 
with open("trends_mysql.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print(" Saved: trends_mysql.sql")
print("   → Open MySQL Workbench → File → Open SQL Script → run it")
