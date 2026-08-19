# RetailPulse — SQL Analytics & Data Quality Engine

An end-to-end analytics project built to demonstrate the core skills required
for a Data Analyst role: SQL, Excel, data quality management, and business
reporting — using a realistic, intentionally messy retail dataset.

## Why this project

Most portfolio projects use a clean dataset and stop at "here's a dashboard."
This one is built the way real analyst work actually happens:

1. The data has real problems (duplicates, orphaned foreign keys, inconsistent
   labels, bad values, stale prices) — and there's a systematic framework to
   detect them, not just eyeballing.
2. The SQL goes beyond `SELECT * WHERE` — window functions, CTEs, and cohort
   analysis that answer real business questions.
3. Query performance is measured and improved, not just written and forgotten.
4. The Excel deliverable is fully formula-driven (SUMIFS, not hardcoded
   numbers), so it recalculates correctly if the underlying data changes —
   the way a report that goes to management actually needs to work.

## Project structure

```
retailpulse/
├── data/
│   └── retailpulse.db                  # SQLite database (generated)
├── scripts/
│   ├── 01_generate_data.py             # builds the messy dataset
│   ├── 02_run_analytics.py             # runs all SQL, exports CSVs
│   ├── 03_query_optimization.py        # EXPLAIN QUERY PLAN before/after indexing
│   └── 04_build_excel_report.py        # builds the formula-driven Excel report
├── sql/
│   ├── 02_advanced_analytics.sql       # 5 advanced business-question queries
│   └── 03_data_quality_checks.sql      # 8 data quality detection queries
└── output/
    ├── RetailPulse_Management_Report.xlsx
    └── *.csv                            # exported query results
```

## How to run it

```bash
cd scripts
python3 01_generate_data.py        # step 1: build the database
python3 02_run_analytics.py        # step 2: run all SQL, export results
python3 03_query_optimization.py   # step 3: see the indexing improvement
python3 04_build_excel_report.py   # step 4: build the Excel report
```

Everything runs on plain Python 3 + SQLite (built-in) + openpyxl — no external
database server or paid software required, so anyone can clone and run it.

## What's inside

### 1. The dataset (`01_generate_data.py`)
A 4-table relational schema (customers, products, orders, order_items) with
~500 customers, 100 products, 3,000 orders, and ~9,000 order line items —
with realistic problems seeded on purpose: duplicate customer records,
inconsistent category/city casing, missing emails, negative quantities,
orphaned foreign keys, and a few future-dated orders.

### 2. Advanced SQL analytics (`sql/02_advanced_analytics.sql`)
| # | Business question | Technique |
|---|---|---|
| Q1 | Is revenue growing month over month? | `LAG()` window function |
| Q2 | Who are our most valuable customers? | `RANK()`, `SUM() OVER()` |
| Q3 | What % of customers stay active after signup? | Cohort retention analysis |
| Q4 | Which categories drive cumulative revenue? | Running total window function |
| Q5 | How often do repeat customers come back? | `LAG()` partitioned by customer |

### 3. Data quality framework (`sql/03_data_quality_checks.sql`)
Eight checks, each tagged with a severity level (CRITICAL/HIGH/MEDIUM/LOW),
covering duplicate records, missing fields, inconsistent categorical values,
referential integrity breaks, invalid numeric values, price mismatches, and
implausible dates — plus a one-query management scorecard that summarizes
every issue found.

### 4. Query optimization (`03_query_optimization.py`)
Runs a realistic multi-table query, captures its `EXPLAIN QUERY PLAN` (shows
a full table `SCAN`), adds two targeted indexes, then re-runs — the plan
changes to an indexed `SEARCH`, with the actual wall-clock time improvement
printed.

### 5. Excel management report (`RetailPulse_Management_Report.xlsx`)
Four sheets, fully formula-driven:
- **Raw_Data** — the underlying fact table
- **Monthly_Summary** — revenue, order count, AOV, and MoM growth via `SUMIFS`
- **Category_Summary** — revenue by category with `SUMIFS` and % of total
- **Data_Quality_Flags** — row-level flags for negative quantities and bad
  prices, computed live via formula, with a summary scorecard

No number in this workbook is hardcoded — every summary cell recalculates
from the raw data sheet, the way a report that has to survive a data refresh
actually needs to.

## What this demonstrates for the JD

Mapped directly to the job posting's requirements:
- *"Analyze data... to identify trends, patterns, and business insights"* → SQL analytics queries
- *"Prepare, clean, and validate datasets"* → data quality framework
- *"Create and maintain reports, dashboards, and data visualizations"* → Excel report
- *"Use Excel and other data analysis tools"* → formula-driven workbook
- *"Assist with SQL queries to extract, manipulate, and organize data"* → advanced SQL
- *"Identify data discrepancies and assist with resolving data quality issues"* → DQ checks
- *"Support the preparation of regular and ad-hoc management reports"* → management report

## Notes on scope

- The Excel workbook is capped at 1,500 raw rows by design — real analysts
  pre-aggregate rather than push an entire fact table through row-level Excel
  formulas. The full ~9,000-row dataset is queried directly via SQL and
  exported to CSV (`output/*.csv`) for anything needing the complete set.
- Dataset is synthetic and randomly generated (seeded for reproducibility) —
  no real customer data is used.
