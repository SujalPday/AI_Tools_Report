import pandas as pd
import numpy as np
import os

os.chdir(r"D:\Work\Projects\AI\OWID")

#  Step 14: Load & Explore OWID Files 

owid_files = {
    'papers'   : 'owid_papers.csv',
    'jobs'     : 'owid_jobs.csv',
    'companies': 'owid_companies.csv'
}

owid_data = {}

for key, filename in owid_files.items():
    if os.path.exists(filename):
        df = pd.read_csv(filename, low_memory=False)
        owid_data[key] = df
    else:
        print(f" File not found: {filename}")

#  Step 15: Clean & Analyse OWID Data 

#  Standardise column names 
owid_data['papers'].rename(columns={
    'Entity'                                    : 'country',
    'Code'                                      : 'code',
    'Year'                                      : 'year',
    'AI scholarly publications - Field: All'    : 'ai_publications'
}, inplace=True)

owid_data['jobs'].rename(columns={
    'Entity'                                                    : 'country',
    'Code'                                                      : 'code',
    'Year'                                                      : 'year',
    'Share of artificial intelligence jobs among all job postings': 'ai_job_share_pct'
}, inplace=True)

owid_data['companies'].rename(columns={
    'Entity'                        : 'country',
    'Code'                          : 'code',
    'Year'                          : 'year',
    'Newly founded AI companies'    : 'new_ai_companies'
}, inplace=True)

#  Step 16: Filter, Save CSVs & Generate MySQL file 

#  Remove regional aggregates — keep only real countries 
regional_keywords = [
    'world', 'asia', 'europe', 'africa', 'america',
    'caribbean', 'oceania', 'cset', 'union', 'income',
    'region', 'north', 'south', 'eastern', 'western',
    'central', 'global'
]

def remove_regions(df, country_col='country'):
    mask = ~df[country_col].str.lower().str.contains(
        '|'.join(regional_keywords), na=False
    )
    return df[mask].reset_index(drop=True)

df_papers    = remove_regions(owid_data['papers'])
df_jobs      = remove_regions(owid_data['jobs'])
df_companies = remove_regions(owid_data['companies'])

print(f"Papers after filter    : {len(df_papers):,} rows")
print(f"Jobs after filter      : {len(df_jobs):,} rows")
print(f"Companies after filter : {len(df_companies):,} rows")

#  Add source column 
df_papers['source']    = 'Our World in Data'
df_jobs['source']      = 'Our World in Data'
df_companies['source'] = 'Our World in Data'

#  Save CSVs 
df_papers.to_csv("owid_papers_clean.csv", index=False)
print("\n Saved: owid_papers_clean.csv")

df_jobs.to_csv("owid_jobs_clean.csv", index=False)
print(" Saved: owid_jobs_clean.csv")

df_companies.to_csv("owid_companies_clean.csv", index=False)
print(" Saved: owid_companies_clean.csv")

#  Generate MySQL .sql file 
sql_lines = []

sql_lines.append("-- ============================================")
sql_lines.append("-- AI TOOLS REPORT — Our World in Data")
sql_lines.append("-- Run this in MySQL Workbench")
sql_lines.append("-- ============================================\n")

sql_lines.append("USE ai_tools_report;\n")

sql_lines.append("-- Clear old data before inserting")
sql_lines.append("DROP TABLE IF EXISTS owid_papers;")
sql_lines.append("DROP TABLE IF EXISTS owid_jobs;")
sql_lines.append("DROP TABLE IF EXISTS owid_companies;\n")

#  Table 1: AI Publications 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS owid_papers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    country         VARCHAR(100),
    code            VARCHAR(10),
    year            INT,
    ai_publications INT,
    source          VARCHAR(50)
);\n""")

sql_lines.append("INSERT INTO owid_papers (country, code, year, ai_publications, source) VALUES")
rows = []
for _, row in df_papers.iterrows():
    country = str(row['country']).replace("'", "\\'")
    code    = str(row['code']).replace("'", "\\'")
    rows.append(
        f"  ('{country}', '{code}', {int(row['year'])}, "
        f"{int(row['ai_publications'])}, 'Our World in Data')"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Table 2: AI Job Share 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS owid_jobs (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    country          VARCHAR(100),
    code             VARCHAR(10),
    year             INT,
    ai_job_share_pct DECIMAL(8,4),
    source           VARCHAR(50)
);\n""")

sql_lines.append("INSERT INTO owid_jobs (country, code, year, ai_job_share_pct, source) VALUES")
rows = []
for _, row in df_jobs.iterrows():
    country = str(row['country']).replace("'", "\\'")
    code    = str(row['code']).replace("'", "\\'")
    rows.append(
        f"  ('{country}', '{code}', {int(row['year'])}, "
        f"{round(float(row['ai_job_share_pct']), 4)}, 'Our World in Data')"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Table 3: New AI Companies 
sql_lines.append("""
CREATE TABLE IF NOT EXISTS owid_companies (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    country          VARCHAR(100),
    code             VARCHAR(10),
    year             INT,
    new_ai_companies INT,
    source           VARCHAR(50)
);\n""")

sql_lines.append("INSERT INTO owid_companies (country, code, year, new_ai_companies, source) VALUES")
rows = []
for _, row in df_companies.iterrows():
    country = str(row['country']).replace("'", "\\'")
    code    = str(row['code']).replace("'", "\\'")
    rows.append(
        f"  ('{country}', '{code}', {int(row['year'])}, "
        f"{int(row['new_ai_companies'])}, 'Our World in Data')"
    )
sql_lines.append(",\n".join(rows) + ";\n")

#  Useful queries 
sql_lines.append("""
-- ============================================
-- USEFUL QUERIES
-- ============================================

-- Top 10 countries by AI publications
SELECT country, SUM(ai_publications) AS total
FROM owid_papers
GROUP BY country
ORDER BY total DESC
LIMIT 10;

-- Global AI job share growth over time
SELECT year, ROUND(AVG(ai_job_share_pct), 3) AS avg_job_share
FROM owid_jobs
GROUP BY year
ORDER BY year;

-- AI companies founded per year globally
SELECT year, SUM(new_ai_companies) AS total_companies
FROM owid_companies
GROUP BY year
ORDER BY year;

-- Latest AI job share by country
SELECT country, ai_job_share_pct
FROM owid_jobs
WHERE year = (SELECT MAX(year) FROM owid_jobs)
ORDER BY ai_job_share_pct DESC;
""")

#  Write file 
with open("owid_mysql.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print(" Saved: owid_mysql.sql")
print("   → Open MySQL Workbench → File → Open SQL Script → run it")