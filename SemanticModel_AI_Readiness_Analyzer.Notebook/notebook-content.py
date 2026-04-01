# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   }
# META }

# MARKDOWN ********************

# ## 🤖 Semantic Model AI Readiness Analyzer
# 
# This notebook checks your Power BI semantic model against the **[best practices for AI-ready semantic models](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices#prep-for-ai-make-semantic-model-ai-ready)** documented by Microsoft, producing a prioritised list of improvements to maximise accuracy when using **Fabric Data Agent** or **Power BI Copilot**.
# 
# ### What's analysed
# 
# | # | Check | Importance |
# |---|-------|------------|
# | 1 | Star schema / relationship structure | 🔴 Critical |
# | 2 | Business-friendly naming | 🟠 Important |
# | 3 | Object descriptions | 🔴 Critical |
# | 4 | Synonyms / linguistic schema | 🟡 Recommended |
# | 5 | Implicit measures (numeric column summarisation) | 🔴 Critical |
# | 6 | Duplicate / overlapping measures | 🟠 Important |
# | 7 | Ambiguous date fields | 🟠 Important |
# | 8 | Hidden objects risk | 🟠 Important |
# | 9 | Model complexity / bloat | 🟡 Recommended |
# | 10 | Prep for AI configuration (AI Schema, Instructions, Verified Answers) | 🔴 Critical |
# | 11 | Best Practice Analyzer — performance & DAX | 🔴 Critical |
# | + | Bonus: Measure dependency analysis | 🟡 Recommended |
# 
# > **Powered by** [Semantic Link](https://learn.microsoft.com/fabric/data-science/semantic-link-overview) and [Semantic Link Labs](https://github.com/microsoft/semantic-link-labs)


# MARKDOWN ********************

# ### 📋 Prerequisites
# - Run inside a **Microsoft Fabric** workspace notebook
# - The semantic model must be published to the same (or an accessible) Fabric workspace
# - You need **Build** (or higher) permissions on the semantic model
# - `semantic-link-labs` will be installed automatically in the next cell

# CELL ********************

# Install required packages
%pip install semantic-link-labs --quiet

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### ⚙️ Step 1 — Set Your Parameters
# Update the two values below, then **Run all cells**.

# CELL ********************

import sempy.fabric as fabric
import pandas as pd
import re
import warnings
warnings.filterwarnings('ignore')
from IPython.display import display, HTML

# ============================================================
# 🔧  PARAMETERS — update these values
# ============================================================
dataset   = "auto_claims_sm"   # Name or ID of your semantic model
workspace = "fabriciq"       # Name or ID of your Fabric workspace
# ============================================================

print(f"Parameters set:  Model = '{dataset}'  |  Workspace = '{workspace}'")
print("Run the next cells to start the analysis ...")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### 📦 Step 2 — Load Semantic Model Metadata

# CELL ********************

print("Loading semantic model metadata ...")
print("-" * 55)

try:
    tables_df        = fabric.list_tables(dataset=dataset, workspace=workspace)
    columns_df       = fabric.list_columns(dataset=dataset, workspace=workspace)
    measures_df      = fabric.list_measures(dataset=dataset, workspace=workspace)
    relationships_df = fabric.list_relationships(dataset=dataset, workspace=workspace)
except Exception as e:
    print(f"ERROR loading metadata: {e}")
    print("Verify the dataset and workspace parameter values and re-run.")
    raise

# Helper: treat any truthy/string 'True' as True for 'Is Hidden'
def is_hidden_mask(df, col='Is Hidden'):
    if col not in df.columns:
        return pd.Series([False] * len(df), index=df.index)
    return df[col].apply(lambda v: str(v).lower() == 'true' if not isinstance(v, bool) else v)

# Filter out auto-generated system tables
SYS_PATTERN = r'^(DateTableTemplate_|LocalDateTable_)'
system_mask = tables_df['Name'].str.match(SYS_PATTERN, na=False)
tables_df   = tables_df[~system_mask].copy()

hidden_tbl_mask = is_hidden_mask(tables_df)
hidden_col_mask = is_hidden_mask(columns_df)
hidden_msr_mask = is_hidden_mask(measures_df)

visible_tables   = tables_df[~hidden_tbl_mask]
visible_columns  = columns_df[~hidden_col_mask]
visible_measures = measures_df[~hidden_msr_mask]

# Remove row-number columns from visible columns
if 'Is Row Number' in columns_df.columns:
    rn_mask = columns_df['Is Row Number'].apply(lambda v: str(v).lower() == 'true' if not isinstance(v, bool) else v)
    visible_columns = visible_columns[~rn_mask[visible_columns.index]]

print(f"Metadata loaded for: '{dataset}'")
print()
print(f"  Visible tables   : {len(visible_tables)}  (total incl. hidden: {len(tables_df)})")
print(f"  Visible columns  : {len(visible_columns)}  (total incl. hidden: {len(columns_df)})")
print(f"  Visible measures : {len(visible_measures)}  (total incl. hidden: {len(measures_df)})")
print(f"  Relationships    : {len(relationships_df)}")

# Global trackers
check_scores = {}  # {check_key: (achieved, max)}
all_issues   = []  # [(severity, description)]  severity: critical | important | recommended

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## ✅ Check 1 — Star Schema Validation
# 
# A **star schema** (fact tables connected to dimension tables via one-to-many relationships) is the recommended structure for AI-ready semantic models. Flat / denormalised tables or pivoted data make it harder for the DAX generation tool to write correct queries.
# 
# **What is checked:**
# - No relationships at all (flat model)
# - Many-to-many relationships
# - Bidirectional cross-filter (use sparingly)
# - Visible tables with no relationships (isolated tables)

# CELL ********************

print("=" * 60)
print("CHECK 1: STAR SCHEMA VALIDATION")
print("=" * 60)

issues_c1  = []
score_c1   = 15

if relationships_df.empty:
    print("CRITICAL: No relationships found — flat/denormalised model detected.")
    print("  This significantly reduces DAX generation accuracy.")
    print("  Refactor into a star schema with clear fact and dimension tables.")
    issues_c1.append(("critical", "No relationships found — flat model detected"))
    score_c1 = 0
else:
    # Many-to-many relationships
    m2m_col = next((c for c in ['Multiplicity', 'Cardinality'] if c in relationships_df.columns), None)
    if m2m_col:
        m2m = relationships_df[
            relationships_df[m2m_col].astype(str).str.contains('ManyToMany|Many.*Many', case=False, na=False)
        ]
        if not m2m.empty:
            print(f"WARNING: {len(m2m)} many-to-many relationship(s) found:")
            for _, r in m2m.iterrows():
                ft = r.get('From Table', 'Unknown')
                tt = r.get('To Table', 'Unknown')
                print(f"   • {ft}  <-->  {tt}")
            print("  DAX accuracy and performance suffer with M:M relationships.")
            print("  Introduce a bridge table to resolve these.")
            issues_c1.append(("important", f"{len(m2m)} many-to-many relationship(s) found"))
            score_c1 -= min(5, len(m2m) * 2)

    # Bidirectional cross-filter
    cf_col = next((c for c in ['Cross Filter Direction', 'Cross Filtering Behavior'] if c in relationships_df.columns), None)
    if cf_col:
        bidir = relationships_df[
            relationships_df[cf_col].astype(str).str.contains('Both', case=False, na=False)
        ]
        if not bidir.empty:
            print(f"WARNING: {len(bidir)} bidirectional relationship(s) (use cautiously).")
            print("  Bidirectional cross-filtering can introduce ambiguity in DAX generation.")
            issues_c1.append(("important", f"{len(bidir)} bidirectional cross-filter relationship(s)"))
            score_c1 -= min(3, len(bidir))

    # Isolated visible tables
    related_tables = set()
    if 'From Table' in relationships_df.columns:
        related_tables = set(relationships_df['From Table'].dropna()) | set(relationships_df['To Table'].dropna())
    visible_tbl_names = set(visible_tables['Name'].dropna())
    isolated = visible_tbl_names - related_tables
    # Exclude common standalone tables (parameter, measure, calc-group)
    isolated = {t for t in isolated if not any(x in t.lower() for x in ['parameter', 'measure', 'calc', 'metric'])}
    if isolated:
        print(f"WARNING: {len(isolated)} visible table(s) with no relationships:")
        for t in sorted(isolated)[:10]:
            print(f"   • {t}")
        print("  Isolated tables confuse the AI — connect or hide them.")
        issues_c1.append(("important", f"{len(isolated)} isolated visible table(s) with no relationships"))
        score_c1 -= min(4, len(isolated) * 2)

    if not issues_c1:
        print("PASSED: Relationship structure is consistent with star schema design.")

score_c1 = max(0, score_c1)
print(f"\nScore: {score_c1}/15")
check_scores['star_schema'] = (score_c1, 15)
all_issues.extend(issues_c1)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🏷️ Check 2 — Business-Friendly Naming
# 
# The DAX generation tool relies on **object names** to interpret natural language questions. Technical names like `TR_AMT`, `DIM_GEO_01`, or `F_SLS` provide no context to the AI. Use clear, business-friendly names that reflect how users naturally describe data.
# 
# > **Example:** Use `Total Revenue` instead of `TR_AMT`, and `Sales Region` instead of `DIM_GEO_01`.

# CELL ********************

print("=" * 60)
print("CHECK 2: BUSINESS-FRIENDLY NAMING")
print("=" * 60)

issues_c2 = []
score_c2  = 10

TECH_PATTERNS = [
    (r'^(DIM|FACT|FCT|STG|SRC|TBL|VW|RPT|TMP|TEMP|LKP|REF|BRG|BRIDGE|MAP|INT|SLV|GLD|GOLD|SILVER|BRONZE|OWN|RAW)_',
     "Database-style prefix (e.g. DIM_, FACT_, STG_)"),
    (r'_(DIM|FACT|FCT|TBL|LKP|REF|SK|NK|AK|BK)$',
     "Database-style suffix"),
    (r'_(AMT|QTY|CNT|CT|NUM|NBR|DT|TS|FLG|FLAG|IND|CD|CODE|KEY|ID)$',
     "Column abbreviation suffix (e.g. _AMT, _QTY, _DT)"),
    (r'^[A-Z][A-Z0-9_]{2,}$',
     "All-uppercase / database-style name"),
    (r'^[A-Za-z0-9]{1,2}$',
     "Very short name (likely an abbreviation)"),
    (r'\d{2,}$',
     "Ends with numbers (e.g. Table01, Column99)"),
    (r'^[A-Za-z]_[A-Z]',
     "Single-letter prefix pattern (e.g. F_SLS)"),
]

def is_technical(name):
    for pattern, reason in TECH_PATTERNS:
        if re.search(pattern, str(name)):
            return True, reason
    return False, None

flagged_tables   = []
flagged_columns  = []
flagged_measures = []

for _, row in visible_tables.iterrows():
    ok, reason = is_technical(row['Name'])
    if ok:
        flagged_tables.append({'Name': row['Name'], 'Reason': reason})

for _, row in visible_columns.iterrows():
    ok, reason = is_technical(row.get('Column Name', ''))
    if ok:
        flagged_columns.append({'Table': row.get('Table Name', ''), 'Column': row.get('Column Name', ''), 'Reason': reason})

for _, row in visible_measures.iterrows():
    ok, reason = is_technical(row.get('Measure Name', ''))
    if ok:
        flagged_measures.append({'Table': row.get('Table Name', ''), 'Measure': row.get('Measure Name', ''), 'Reason': reason})

total_flagged  = len(flagged_tables) + len(flagged_columns) + len(flagged_measures)
total_visible  = len(visible_tables) + len(visible_columns) + len(visible_measures)

if total_flagged == 0:
    print("PASSED: All visible object names appear business-friendly.")
else:
    pct = total_flagged / max(total_visible, 1) * 100
    score_c2 = max(0, int(10 - pct / 10))

    if flagged_tables:
        print(f"WARNING: {len(flagged_tables)} table(s) with technical-style names:")
        for item in flagged_tables[:10]:
            print(f"   • '{item['Name']}'  →  {item['Reason']}")
        if len(flagged_tables) > 10:
            print(f"   ... and {len(flagged_tables) - 10} more")

    if flagged_columns:
        print(f"\nWARNING: {len(flagged_columns)} column(s) with technical-style names:")
        for item in flagged_columns[:15]:
            print(f"   • '{item['Table']}[{item['Column']}]'  →  {item['Reason']}")
        if len(flagged_columns) > 15:
            print(f"   ... and {len(flagged_columns) - 15} more")

    if flagged_measures:
        print(f"\nWARNING: {len(flagged_measures)} measure(s) with technical-style names:")
        for item in flagged_measures[:15]:
            print(f"   • '{item['Table']}[{item['Measure']}]'  →  {item['Reason']}")
        if len(flagged_measures) > 15:
            print(f"   ... and {len(flagged_measures) - 15} more")

    print("\nTIP: Use the Power BI Modeling MCP server to generate business-friendly")
    print("     names automatically: https://github.com/microsoft/powerbi-modeling-mcp")
    print("     Review and validate changes before saving to avoid breaking DAX expressions.")
    issues_c2.append(("important", f"{total_flagged} object(s) with technical / non-descriptive names"))

print(f"\nScore: {score_c2}/10")
check_scores['naming'] = (score_c2, 10)
all_issues.extend(issues_c2)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 📝 Check 3 — Object Descriptions
# 
# Descriptions on tables, columns, and measures are **critical** for AI accuracy. The DAX generation tool uses them to understand the purpose and context of each object. Every object you include in your AI Data Schema **must** have a clear description.
# 
# > **Tip:** Use `sempy_labs.update_column_properties()` or `.update_measure()` to add descriptions programmatically at scale.

# CELL ********************

print("=" * 60)
print("CHECK 3: OBJECT DESCRIPTIONS")
print("=" * 60)

issues_c3 = []
score_c3  = 15

def missing_desc_mask(df, col='Description'):
    if col not in df.columns:
        return pd.Series([True] * len(df), index=df.index)
    return df[col].isna() | (df[col].astype(str).str.strip() == '')

tables_no_desc   = visible_tables[missing_desc_mask(visible_tables)]
cols_no_desc     = visible_columns[missing_desc_mask(visible_columns)]
measures_no_desc = visible_measures[missing_desc_mask(visible_measures)]

tbl_cov = 1 - len(tables_no_desc)   / max(len(visible_tables),   1)
col_cov = 1 - len(cols_no_desc)     / max(len(visible_columns),  1)
msr_cov = 1 - len(measures_no_desc) / max(len(visible_measures), 1)

print(f"  Description Coverage:")
print(f"  Tables   : {len(visible_tables)   - len(tables_no_desc)}/{len(visible_tables)}   ({tbl_cov*100:.0f}%)")
print(f"  Columns  : {len(visible_columns)  - len(cols_no_desc)}/{len(visible_columns)}  ({col_cov*100:.0f}%)")
print(f"  Measures : {len(visible_measures) - len(measures_no_desc)}/{len(visible_measures)}  ({msr_cov*100:.0f}%)")
print()

total_missing = len(tables_no_desc) + len(cols_no_desc) + len(measures_no_desc)
total_objects = len(visible_tables) + len(visible_columns) + len(visible_measures)

if total_missing == 0:
    print("PASSED: All visible objects have descriptions.")
else:
    overall_cov  = 1 - total_missing / max(total_objects, 1)
    score_c3     = max(0, int(15 * overall_cov))

    if not tables_no_desc.empty:
        print(f"MISSING DESCRIPTIONS — {len(tables_no_desc)} table(s):")
        for name in tables_no_desc['Name'].tolist()[:10]:
            print(f"   • {name}")
        if len(tables_no_desc) > 10:
            print(f"   ... and {len(tables_no_desc) - 10} more")

    if not cols_no_desc.empty:
        print(f"\nMISSING DESCRIPTIONS — {len(cols_no_desc)} column(s) (showing first 20):")
        for _, row in cols_no_desc.head(20).iterrows():
            print(f"   • {row.get('Table Name', '?')}[{row.get('Column Name', '?')}]")
        if len(cols_no_desc) > 20:
            print(f"   ... and {len(cols_no_desc) - 20} more")

    if not measures_no_desc.empty:
        print(f"\nMISSING DESCRIPTIONS — {len(measures_no_desc)} measure(s) (showing first 20):")
        for _, row in measures_no_desc.head(20).iterrows():
            print(f"   • {row.get('Table Name', '?')}[{row.get('Measure Name', '?')}]")
        if len(measures_no_desc) > 20:
            print(f"   ... and {len(measures_no_desc) - 20} more")

    print("\nACTION: Add descriptions in Power BI Desktop → Data view → Properties pane.")
    print("  At minimum, describe all objects included in your AI Data Schema.")
    print("  Programmatic bulk update: sempy_labs.update_column_properties() / .update_measure()")
    issues_c3.append(("critical", f"{total_missing} visible object(s) missing descriptions"))

print(f"\nScore: {score_c3}/15")
check_scores['descriptions'] = (score_c3, 15)
all_issues.extend(issues_c3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🔤 Check 4 — Synonyms / Linguistic Schema
# 
# Synonyms allow the AI to match natural-language variations to your objects. For example, adding `revenue` and `income` as synonyms for a `Total Sales` measure helps the AI respond correctly regardless of which term a user chooses.
# 
# > **Reference:** [Q&A linguistic schema best practices](https://learn.microsoft.com/power-bi/natural-language/q-and-a-best-practices)

# CELL ********************

print("=" * 60)
print("CHECK 4: SYNONYMS / LINGUISTIC SCHEMA")
print("=" * 60)

issues_c4 = []
score_c4  = 5

try:
    from sempy_labs.tom import connect_semantic_model

    tbl_with_syn = 0
    col_with_syn = 0
    msr_with_syn = 0
    msrs_without = []

    with connect_semantic_model(dataset=dataset, workspace=workspace, readonly=True) as tom:
        for table in tom.model.Tables:
            if table.Name.startswith(('DateTableTemplate_', 'LocalDateTable_')):
                continue
            if table.IsHidden:
                continue
            if list(table.Synonyms):
                tbl_with_syn += 1
            for col in table.Columns:
                if col.IsHidden:
                    continue
                if list(col.Synonyms):
                    col_with_syn += 1
            for msr in table.Measures:
                if msr.IsHidden:
                    continue
                if list(msr.Synonyms):
                    msr_with_syn += 1
                else:
                    msrs_without.append(f"{table.Name}[{msr.Name}]")

    total_syn = tbl_with_syn + col_with_syn + msr_with_syn
    if total_syn > 0:
        print(f"Synonyms configured on:")
        print(f"   Tables   : {tbl_with_syn}")
        print(f"   Columns  : {col_with_syn}")
        print(f"   Measures : {msr_with_syn}")
        if msrs_without:
            pct_covered = 1 - len(msrs_without) / max(len(visible_measures), 1)
            score_c4 = max(2, int(5 * pct_covered))
            print(f"\nWARNING: {len(msrs_without)} visible measure(s) have no synonyms (showing first 10):")
            for m in msrs_without[:10]:
                print(f"   • {m}")
            issues_c4.append(("recommended", f"{len(msrs_without)} visible measure(s) have no synonyms"))
        else:
            print("\nPASSED: All visible measures have synonyms configured.")
    else:
        print("WARNING: No synonyms found on any object.")
        print("  Adding synonyms improves AI accuracy when users use different terminology.")
        score_c4 = 1
        issues_c4.append(("recommended", "No synonyms configured on any visible object"))

except Exception as e:
    print(f"INFO: Could not inspect synonyms via TOM — {e}")
    print("  Manual check: Power BI Desktop → Data view → select object → Properties pane → Synonyms")
    print("  Or manage the linguistic schema YAML file for bulk updates.")
    score_c4 = 3  # Unknown state — partial credit

print("\nTIP: Add synonyms for key measures and dimensions, including:")
print("   - Alternative business terms  (revenue / sales / income)")
print("   - Common abbreviations        (YTD, Q4, MTD)")
print("   - Departmental terminology    (headcount = employees)")
print(f"\nScore: {score_c4}/5")
check_scores['synonyms'] = (score_c4, 5)
all_issues.extend(issues_c4)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🔢 Check 5 — Implicit Measures (Numeric Column Summarisation)
# 
# Numeric columns with a default summarisation (Sum, Average, Count, …) create **implicit measures** when used in visuals or queries. These produce unpredictable results and should be avoided. For every numeric column:
# - Set **Summarisation = None** (Don't summarise) to prevent unintended aggregations, **and**
# - Create explicit DAX measures for any calculations you need.
# 
# > **Common pitfall:** Leaving `SalesAmount` as a column with Sum summarisation — the AI may aggregate it in unexpected ways.

# CELL ********************

print("=" * 60)
print("CHECK 5: IMPLICIT MEASURES (NUMERIC SUMMARISATION)")
print("=" * 60)

issues_c5 = []
score_c5  = 10

NUMERIC_TYPES   = ['Int64', 'Double', 'Decimal', 'Currency', 'Single',
                   'Whole number', 'Decimal number', 'Fixed decimal number']
SAFE_SUMMARISE  = {'None', 'DoNotSummarize', 'none', 'Do Not Summarize',
                   'donotsummarize', 'Don\'t summarize'}

if 'Summarize By' not in columns_df.columns:
    print("INFO: 'Summarize By' column not found — skipping this check.")
    print("  Manually verify: Power BI Desktop → Data view → select numeric column → Column tools → Summarization")
    score_c5 = 5
else:
    num_vis_cols = visible_columns[
        visible_columns['Data Type'].isin(NUMERIC_TYPES)
    ]

    implicit = num_vis_cols[
        ~num_vis_cols['Summarize By'].astype(str).isin(SAFE_SUMMARISE) &
        num_vis_cols['Summarize By'].notna()
    ]

    if implicit.empty:
        print("PASSED: All visible numeric columns have Summarize By = None.")
        print("  No implicit measure risks detected.")
    else:
        pct      = len(implicit) / max(len(num_vis_cols), 1) * 100
        score_c5 = max(0, int(10 - pct / 10))

        print(f"WARNING: {len(implicit)} visible numeric column(s) with implicit summarisation:")
        print()
        for tbl, grp in implicit.groupby('Table Name'):
            print(f"  Table: {tbl}")
            for _, row in grp.iterrows():
                print(f"    • {row.get('Column Name','?')}  (Type: {row.get('Data Type','?')}, Summarize By: {row.get('Summarize By','?')})")

        print("\nACTION: Set Summarization = 'Don't summarize' for these columns.")
        print("  Power BI Desktop → Data view → select column → Column tools → Summarization → 'Don't summarize'")
        print("  Create explicit DAX measures for any calculations you need.")
        issues_c5.append(("critical", f"{len(implicit)} visible numeric column(s) with implicit summarisation"))

print(f"\nScore: {score_c5}/10")
check_scores['implicit_measures'] = (score_c5, 10)
all_issues.extend(issues_c5)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🔄 Check 6 — Duplicate / Overlapping Measures
# 
# Multiple measures that calculate **similar metrics** (e.g. `Total Sales`, `Sales Amount`, `Revenue`) create ambiguity — the AI may choose the wrong one. Consolidate duplicates or clearly differentiate them, and in your AI Data Schema include only the **canonical** measure for each business concept.
# 
# > **Common pitfall:** Having `Total Revenue`, `Gross Sales`, `Net Sales`, and `Sales After Returns` all visible — the AI will guess which one to use.

# CELL ********************

print("=" * 60)
print("CHECK 6: DUPLICATE / OVERLAPPING MEASURES")
print("=" * 60)

issues_c6    = []
score_c6     = 5
vis_msr_list = visible_measures['Measure Name'].dropna().tolist()

# Semantic overlap groups — flag if more than 3 measures match the same theme
OVERLAP_GROUPS = {
    "Sales / Revenue"   : r'\b(sales?|revenue?|income|turnover|proceeds|gross)\b',
    "Quantity / Count"  : r'\b(qty|quantity|count|cnt|units?|number|volume)\b',
    "Amount / Value"    : r'\b(amoun?t?|val(ue)?|total|sum|aggregate)\b',
    "Cost / Expense"    : r'\b(cost|expense?|spend|expend|expenditure)\b',
    "Profit / Margin"   : r'\b(profit|margin|ebitda|ebit|earnings?|gain|net)\b',
    "Budget / Target"   : r'\b(budget|target|forecast|plan|goal|quota)\b',
    "YTD / MTD / QTD"   : r'\b(ytd|mtd|qtd|year.to.date|month.to.date|quarter.to.date)\b',
    "Previous Period"   : r'\b(prev(ious)?|last|prior|ly[^a-z])\b',
}

overlapping = {}
for group, pattern in OVERLAP_GROUPS.items():
    matched = [m for m in vis_msr_list if re.search(pattern, m, re.IGNORECASE)]
    if len(matched) > 3:
        overlapping[group] = matched

# Near-identical names (normalised comparison)
def normalise(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

normalised_map = {}
for m in vis_msr_list:
    key = normalise(m)
    normalised_map.setdefault(key, []).append(m)
near_dupes = {k: v for k, v in normalised_map.items() if len(v) > 1}

if not overlapping and not near_dupes:
    print("PASSED: No obvious duplicate or overlapping measures detected.")
else:
    if overlapping:
        score_c6 = max(0, 5 - len(overlapping))
        print(f"WARNING: {len(overlapping)} semantic overlap group(s) with >3 measures:")
        for group, measures in overlapping.items():
            print(f"\n  Group: '{group}'  ({len(measures)} measures)")
            for m in sorted(measures)[:8]:
                print(f"    • {m}")
            if len(measures) > 8:
                print(f"    ... and {len(measures) - 8} more")
        issues_c6.append(("important", f"Measure overlap in {len(overlapping)} semantic group(s) — too many similar measures"))

    if near_dupes:
        print(f"\nWARNING: {len(near_dupes)} near-identical measure name pair(s):")
        for _, mlist in near_dupes.items():
            print(f"   • {mlist}")
        score_c6 = max(0, score_c6 - len(near_dupes))
        issues_c6.append(("critical", f"{len(near_dupes)} near-duplicate measure name(s) found"))

    print("\nACTION:")
    print("  1. Review measures in each flagged group — consolidate or remove redundant ones.")
    print("  2. Add clear descriptions to differentiate measures that must coexist.")
    print("  3. In your AI Data Schema, include ONLY the canonical measure per business concept.")
    print("  4. Hide helper / intermediate measures from report view.")

print(f"\nScore: {score_c6}/5")
check_scores['duplicate_measures'] = (score_c6, 5)
all_issues.extend(issues_c6)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 📅 Check 7 — Ambiguous Date Fields
# 
# Multiple date columns (e.g. `Order Date`, `Ship Date`, `Due Date`, `Fiscal Quarter`, `Calendar Quarter`) without clear guidance **confuse the AI**. When users ask time-based questions the AI may select the wrong date column. Use **AI Instructions** in Prep for AI and **Verified Answers** to specify which date to use by default.
# 
# > **Common pitfall:** Model has 8 date columns and the AI guesses `Due Date` when users mean `Order Date`.

# CELL ********************

print("=" * 60)
print("CHECK 7: AMBIGUOUS DATE FIELDS")
print("=" * 60)

issues_c7 = []
score_c7  = 5

DATE_TYPES = ['DateTime', 'Date', 'DateTimeOffset']

date_cols = visible_columns[
    visible_columns['Data Type'].isin(DATE_TYPES) |
    visible_columns['Data Type'].astype(str).str.lower().str.contains('date', na=False)
]

def desc_status(row):
    d = row.get('Description', '')
    return "has description" if d and str(d).strip() else "NO description"

if date_cols.empty:
    print("OK: No visible date columns found. Date columns may be hidden (role-playing dim design).")
elif len(date_cols) == 1:
    r = date_cols.iloc[0]
    print(f"PASSED: Single visible date column: {r.get('Table Name')}[{r.get('Column Name')}] — {desc_status(r)}")
elif len(date_cols) <= 3:
    print(f"INFO: {len(date_cols)} date columns found (low ambiguity risk):")
    for _, row in date_cols.iterrows():
        print(f"   • {row.get('Table Name')}[{row.get('Column Name')}]  —  {desc_status(row)}")
    print("  Consider adding AI Instructions to specify the default date for common questions.")
    score_c7 = 4
else:
    print(f"WARNING: {len(date_cols)} visible date column(s) — HIGH ambiguity risk!")
    print()
    for tbl, grp in date_cols.groupby('Table Name'):
        print(f"  Table: {tbl}")
        for _, row in grp.iterrows():
            print(f"    • {row.get('Column Name')}  ({desc_status(row)})")

    score_c7 = max(0, 5 - max(0, len(date_cols) - 3))
    issues_c7.append(("important", f"{len(date_cols)} visible date columns without clear AI guidance"))

    print("\nACTION:")
    print("  1. Hide date columns that users should not query directly.")
    print("  2. Add descriptions clarifying each date column's purpose.")
    print("  3. Prep for AI → AI Instructions:")
    print("     Example: 'When the user asks about dates, use [Order Date] by default.'")
    print("  4. Create Verified Answers for your most common time-based questions.")

print(f"\nScore: {score_c7}/5")
check_scores['date_fields'] = (score_c7, 5)
all_issues.extend(issues_c7)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 👁️ Check 8 — Hidden Objects Risk
# 
# Hidden columns and tables have specific implications for AI:
# - **Verified Answers break silently** if they reference hidden columns — always use visible columns in Verified Answers.
# - Hidden columns with no descriptions cannot be understood by any downstream process.
# 
# > **Reference:** [Verified Answers documentation](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers)

# CELL ********************

print("=" * 60)
print("CHECK 8: HIDDEN OBJECTS RISK")
print("=" * 60)

issues_c8 = []
score_c8  = 5

hidden_tables   = tables_df[is_hidden_mask(tables_df)]
hidden_columns  = columns_df[is_hidden_mask(columns_df)]
hidden_measures = measures_df[is_hidden_mask(measures_df)]

print(f"  Hidden objects summary:")
print(f"    Tables   : {len(hidden_tables)}")
print(f"    Columns  : {len(hidden_columns)}")
print(f"    Measures : {len(hidden_measures)}")
print()

# Hidden columns without descriptions — double risk
if not hidden_columns.empty:
    hc_no_desc = hidden_columns[
        hidden_columns['Description'].isna() | (hidden_columns['Description'].astype(str).str.strip() == '')
    ] if 'Description' in hidden_columns.columns else hidden_columns

    pct = len(hc_no_desc) / max(len(hidden_columns), 1) * 100

    if pct > 50:
        print(f"WARNING: {len(hc_no_desc)} hidden column(s) lack descriptions ({pct:.0f}% of hidden columns).")
        print("  If any of these are referenced by Verified Answers, the answer will silently fail.")
        score_c8 = 3
        issues_c8.append(("important", f"{len(hc_no_desc)} hidden columns without descriptions — Verified Answers risk"))
    else:
        print(f"PASSED: Most hidden columns have descriptions ({100-pct:.0f}% coverage).")
else:
    print("PASSED: No hidden columns found.")

print("\nREMINDER: Verified Answers will NOT work if they reference hidden columns.")
print("  Ensure all columns referenced in Verified Answers are VISIBLE in the model.")

print(f"\nScore: {score_c8}/5")
check_scores['hidden_objects'] = (score_c8, 5)
all_issues.extend(issues_c8)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 📦 Check 9 — Model Complexity / Bloat
# 
# Large models with unnecessary columns, tables, and measures create **noise** for the DAX generation tool, reducing accuracy and increasing response latency. Helper / intermediate measures that are visible also confuse the AI.
# 
# **Approximate thresholds:**
# - > 500 visible columns → configure a focused AI Data Schema
# - > 150 visible measures → review for helper / intermediate measures
# - Visible helper measures → should be hidden or excluded from the AI Data Schema

# CELL ********************

print("=" * 60)
print("CHECK 9: MODEL COMPLEXITY / BLOAT")
print("=" * 60)

issues_c9 = []
score_c9  = 5

vis_tbl_n = len(visible_tables)
vis_col_n = len(visible_columns)
vis_msr_n = len(visible_measures)

print(f"  Visible tables   : {vis_tbl_n}")
print(f"  Visible columns  : {vis_col_n}")
print(f"  Visible measures : {vis_msr_n}")
print()

# Detect helper measures that are visible (they should be hidden)
HELPER_PATTERN = r'\b(helper|_h$|aux|auxiliary|temp|tmp|working|intermediate|_int$|__[a-z])\b'
visible_helpers = visible_measures[
    visible_measures['Measure Name'].astype(str).str.lower().str.contains(HELPER_PATTERN, regex=True, na=False)
]

if not visible_helpers.empty:
    print(f"WARNING: {len(visible_helpers)} potentially visible helper/intermediate measure(s):")
    for _, row in visible_helpers.head(10).iterrows():
        print(f"   • {row.get('Table Name')}[{row.get('Measure Name')}]")
    print("  Helper measures should be hidden or excluded from your AI Data Schema.")
    issues_c9.append(("important", f"{len(visible_helpers)} visible helper/intermediate measure(s)"))
    score_c9 -= 2

if vis_col_n > 500:
    print(f"WARNING: {vis_col_n} visible columns — high noise risk for the AI.")
    print("  Use Prep for AI → AI Data Schema to define a focused subset.")
    issues_c9.append(("recommended", f"High visible column count ({vis_col_n}) — configure AI Data Schema"))
    score_c9 -= 1

if vis_msr_n > 150:
    print(f"WARNING: {vis_msr_n} visible measures — review for redundant intermediate measures.")
    print("  Hide intermediate measures used only as building blocks for other measures.")
    issues_c9.append(("recommended", f"High visible measure count ({vis_msr_n}) — review for redundancy"))
    score_c9 -= 1

if not issues_c9:
    print("PASSED: Model complexity is manageable for AI use.")

print("\nTIP: Use Best Practice Analyzer and Memory Analyzer in Fabric notebooks to identify")
print("     unnecessary columns, high-cardinality columns, and inefficient DAX patterns.")
print("     Reference: https://learn.microsoft.com/power-bi/transform-model/service-notebooks")

score_c9 = max(0, score_c9)
print(f"\nScore: {score_c9}/5")
check_scores['model_bloat'] = (score_c9, 5)
all_issues.extend(issues_c9)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🤖 Check 10 — Prep for AI Configuration
# 
# **This is the most impactful configuration for AI accuracy.** Power BI's [Prep for AI](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai) feature provides three components your model needs:
# 
# | Component | Purpose | Where to configure |
# |-----------|---------|-------------------|
# | **AI Data Schema** | Define which tables/columns/measures the AI should use | Prep data for AI → Simplify data schema |
# | **AI Instructions** | Business terminology, default dates, metric preferences | Prep data for AI → Add AI instructions |
# | **Verified Answers** | Pre-approved responses for common/complex questions | Prep data for AI → Verified answers |
# 
# > ⚠️ **Important:** The DAX generation tool used by Fabric Data Agent relies **solely** on the semantic model metadata and Prep for AI configuration. Instructions added at the data agent level are **ignored** for DAX generation.
# 
# > 📍 **Access:** In Power BI Desktop or Service → **Home ribbon → Prep data for AI**


# CELL ********************

print("=" * 60)
print("CHECK 10: PREP FOR AI CONFIGURATION")
print("=" * 60)
print()

issues_c10 = []
score_c10  = 15  # 5 pts per component

config_status = {
    'ai_data_schema'  : {'found': False, 'label': 'AI Data Schema',  'pts': 5, 'detail': ''},
    'ai_instructions' : {'found': False, 'label': 'AI Instructions', 'pts': 5, 'detail': ''},
    'verified_answers': {'found': False, 'label': 'Verified Answers','pts': 5, 'detail': ''},
}

try:
    from sempy_labs.tom import connect_semantic_model

    with connect_semantic_model(dataset=dataset, workspace=workspace, readonly=True) as tom:
        model = tom.model

        # Model-level annotations
        model_annotations = {ann.Name: ann.Value for ann in model.Annotations}

        for ann_name, ann_val in model_annotations.items():
            upper = ann_name.upper()
            if any(k in upper for k in ['AI_INSTRUCTION', 'AIINSTRUCTION', 'PREP_AI_INSTRUCTION',
                                          'COPILOT_INSTRUCTION', 'PBI_AI_INSTRUCTION']):
                config_status['ai_instructions']['found'] = True
                config_status['ai_instructions']['detail'] = f"annotation '{ann_name}'"
            if any(k in upper for k in ['VERIFIED', 'VERIFIED_ANSWER', 'COPILOT_VERIFIED_ANSWER',
                                          'PBI_VERIFIED']):
                config_status['verified_answers']['found'] = True
                config_status['verified_answers']['detail'] = f"annotation '{ann_name}'"
            if any(k in upper for k in ['AI_SCHEMA', 'AISCHEMA', 'DATA_AGENT_SCHEMA',
                                          'PREP_AI_SCHEMA', 'COPILOT_SCHEMA', 'PBI_AI_SCHEMA']):
                config_status['ai_data_schema']['found'] = True
                config_status['ai_data_schema']['detail'] = f"model annotation '{ann_name}'"

        # Table/column-level annotations for AI schema markers
        for table in model.Tables:
            if table.Name.startswith(('DateTableTemplate_', 'LocalDateTable_')):
                continue
            for ann in table.Annotations:
                if any(k in ann.Name.upper() for k in ['AI_SCHEMA', 'AISCHEMA', 'COPILOT_SCHEMA',
                                                         'AI_DATA_SCHEMA', 'PREP_SCHEMA']):
                    config_status['ai_data_schema']['found'] = True
                    config_status['ai_data_schema']['detail'] = f"table annotation on '{table.Name}'"
                    break
            for col in table.Columns:
                for ann in col.Annotations:
                    if any(k in ann.Name.upper() for k in ['AI_SCHEMA', 'AISCHEMA', 'COPILOT_SCHEMA']):
                        config_status['ai_data_schema']['found'] = True
                        config_status['ai_data_schema']['detail'] = f"column annotation on '{table.Name}[{col.Name}]'"
                        break

    print("TOM annotation scan results (best-effort detection):")
    print()

except Exception as e:
    print(f"INFO: Could not scan TOM annotations — {e}")
    print("  Manual verification is required (see checklist below).")
    print()

# Display status table
print(f"  {'Component':<35} {'Status'}")
print(f"  {'─'*35} {'─'*25}")
for key, info in config_status.items():
    icon   = "Detected" if info['found'] else "Not detected"
    detail = f" ({info['detail']})" if info['detail'] else ""
    print(f"  {info['label']:<35} {icon}{detail}")

print()
print("=" * 60)
print("MANUAL CHECKLIST — verify in Power BI Desktop or Service")
print("Home ribbon > Prep data for AI")
print("=" * 60)
print()
print("1. AI DATA SCHEMA  (Simplify data schema tab)")
print("   [ ] Select only tables/columns/measures your agent should answer")
print("   [ ] Include ALL dependent objects (see Measure Dependency check below)")
print("   [ ] Match schema selection with tables used in Fabric Data Agent")
print("   [ ] Use business-friendly names for all selected objects")
print("   [ ] For large models: start narrow and expand based on test results")
print()
print("2. AI INSTRUCTIONS  (Add AI instructions tab)")
print("   [ ] Define business terminology")
print("       Example: 'Top performer = sales rep achieving 110%+ of monthly quota'")
print("   [ ] Specify default date field")
print("       Example: 'Use Order Date unless the user specifies otherwise'")
print("   [ ] Set metric preferences")
print("       Example: 'For profitability questions, use Contribution Margin, not Gross Profit'")
print("   [ ] Define data source routing")
print("       Example: 'For inventory questions, prioritise Warehouse_Inventory table'")
print("   [ ] Keep instructions focused — avoid contradictions and excessive complexity")
print("   NOTE: Do NOT put semantic-model instructions in the Data Agent instructions field")
print("         — they are ignored by the DAX generation tool.")
print()
print("3. VERIFIED ANSWERS")
print("   [ ] Create verified answers for your 5-10 most common questions")
print("   [ ] Use 5-7 trigger questions per verified answer")
print("   [ ] Include both formal and conversational phrasings")
print("   [ ] Configure up to 3 filters per verified answer")
print("   [ ] Only reference VISIBLE columns (hidden columns break verified answers)")
print("   [ ] After renaming objects, re-save affected verified answers")

# Score calculation
for key, info in config_status.items():
    if not info['found']:
        score_c10 -= info['pts']
        issues_c10.append(("critical", f"Prep for AI: '{info['label']}' not detected — manual verification required"))

score_c10 = max(0, score_c10)
print(f"\nScore: {score_c10}/15  (annotation-based detection — verify manually above)")
check_scores['prep_for_ai'] = (score_c10, 15)
all_issues.extend(issues_c10)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## ⚡ Check 11 — Best Practice Analyzer (Performance & DAX Quality)
# 
# The [Best Practice Analyzer](https://learn.microsoft.com/python/api/semantic-link-sempy/sempy.fabric#sempy-fabric-run-model-bpa) (BPA) checks 60+ rules for **performance, DAX quality, error prevention, and model design**. Poor model performance directly impacts AI response times — users expect quick conversational answers.
# 
# > Slow models = slow AI responses. A well-optimised model also creates less noise for the DAX generation tool.

# CELL ********************

print("=" * 60)
print("CHECK 11: BEST PRACTICE ANALYZER (PERFORMANCE & DAX)")
print("=" * 60)
print()

issues_c11 = []
score_c11  = 10

try:
    import sempy_labs as labs
    bpa_results = labs.run_model_bpa(dataset=dataset, workspace=workspace)

    if bpa_results is not None and not bpa_results.empty:
        sev_col = 'Severity' if 'Severity' in bpa_results.columns else None
        print(f"BPA Results: {len(bpa_results)} recommendation(s) found")
        if sev_col:
            for sev, cnt in bpa_results[sev_col].value_counts().items():
                print(f"   {sev}: {cnt}")

        if   len(bpa_results) >= 20: score_c11 = 2
        elif len(bpa_results) >= 10: score_c11 = 5
        elif len(bpa_results) >= 5:  score_c11 = 7
        elif len(bpa_results) >= 1:  score_c11 = 8

        print()
        display(bpa_results)
        issues_c11.append(("important", f"BPA found {len(bpa_results)} recommendation(s) for performance & DAX quality"))
    else:
        print("PASSED: No BPA issues found!")

except Exception:
    try:
        print("Falling back to built-in BPA via sempy.fabric ...")
        fabric.run_model_bpa(dataset=dataset, workspace=workspace)
        score_c11 = 8
    except Exception as e2:
        print(f"Could not run BPA: {e2}")
        print("  Run manually: fabric.run_model_bpa(dataset=dataset, workspace=workspace)")
        score_c11 = 5

print(f"\nScore: {score_c11}/10")
check_scores['bpa'] = (score_c11, 10)
all_issues.extend(issues_c11)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🔗 Bonus — Measure Dependency Analysis
# 
# Before configuring your AI Data Schema, use `get_measure_dependencies` to identify **all** tables, columns, and measures that a given measure depends on. Include every dependent object in your schema — missing dependencies cause incorrect DAX generation.
# 
# > **Reference:** [get_measure_dependencies](https://semantic-link-labs.readthedocs.io/en/stable/sempy_labs.html#sempy_labs.get_measure_dependencies)

# CELL ********************

print("=" * 60)
print("BONUS: MEASURE DEPENDENCY ANALYSIS")
print("=" * 60)
print()
print("Use this table to ensure ALL dependent objects are included in your AI Data Schema.")
print()

try:
    from sempy_labs import get_measure_dependencies
    deps = get_measure_dependencies(dataset=dataset, workspace=workspace)

    if deps is not None and not deps.empty:
        n_measures = deps['Measure Name'].nunique() if 'Measure Name' in deps.columns else len(deps)
        print(f"Dependency data retrieved for {n_measures} measure(s).")
        print("Showing first 30 rows:")
        print()
        display(deps.head(30))
        print()
        print("TIP: When configuring Prep for AI > AI Data Schema, include ALL tables,")
        print("     columns, and measures listed as dependencies for your selected measures.")
    else:
        print("INFO: No dependency data returned.")

except ImportError:
    print("INFO: get_measure_dependencies not available — upgrade sempy_labs.")
    print("  %pip install semantic-link-labs --upgrade")
except Exception as e:
    print(f"INFO: Could not compute measure dependencies — {e}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🏆 AI Readiness Scorecard

# CELL ********************

print()
print("=" * 68)
print("   🤖  SEMANTIC MODEL AI READINESS SCORECARD")
print(f"       Model: {dataset}  |  Workspace: {workspace}")
print("=" * 68)
print()

total_achieved = sum(v[0] for v in check_scores.values())
total_max      = sum(v[1] for v in check_scores.values())
score_pct      = (total_achieved / total_max * 100) if total_max > 0 else 0

LABELS = {
    'star_schema'       : ('Star Schema Validation',                   15),
    'naming'            : ('Business-Friendly Naming',                 10),
    'descriptions'      : ('Object Descriptions',                      15),
    'synonyms'          : ('Synonyms / Linguistic Schema',              5),
    'implicit_measures' : ('Implicit Measures',                        10),
    'duplicate_measures': ('Duplicate / Overlapping Measures',          5),
    'date_fields'       : ('Ambiguous Date Fields',                     5),
    'hidden_objects'    : ('Hidden Objects Risk',                       5),
    'model_bloat'       : ('Model Complexity / Bloat',                  5),
    'prep_for_ai'       : ('Prep for AI Configuration',                15),
    'bpa'               : ('Best Practice Analyzer',                   10),
}

print(f"  {'Check':<43} {'Score':>8}   Progress")
print("  " + "─" * 64)

for key, (label, max_pts) in LABELS.items():
    if key in check_scores:
        achieved, _  = check_scores[key]
        pct          = achieved / max_pts * 100 if max_pts > 0 else 0
        bar_fill     = int(pct / 5)
        bar          = "█" * bar_fill + "░" * (20 - bar_fill)
        icon         = "✅" if pct >= 80 else ("⚠️ " if pct >= 50 else "❌")
        print(f"  {icon} {label:<42} {achieved:>3}/{max_pts:<3}  {bar}")

print("  " + "─" * 64)
print(f"  {'TOTAL SCORE':<45} {total_achieved:>3}/{total_max:<3}  ({score_pct:.0f}%)")
print()

if   score_pct >= 90: rating, comment = "🟢 AI READY",           "Well-optimised. Monitor and iterate continuously."
elif score_pct >= 70: rating, comment = "🟡 MOSTLY READY",       "Good foundation — address flagged items to maximise accuracy."
elif score_pct >= 50: rating, comment = "🟠 NEEDS IMPROVEMENT",  "Address critical items before deploying to production."
else:                 rating, comment = "🔴 NOT READY",          "Significant improvements needed before using with Fabric Data Agent."

print(f"  Rating : {rating}")
print(f"  Summary: {comment}")
print()

# Prioritised issue list
critical_issues    = [(s, d) for s, d in all_issues if s == 'critical']
important_issues   = [(s, d) for s, d in all_issues if s == 'important']
recommended_issues = [(s, d) for s, d in all_issues if s == 'recommended']

if critical_issues:
    print("  🔴 CRITICAL — Fix immediately:")
    for _, desc in critical_issues:
        print(f"     • {desc}")
    print()

if important_issues:
    print("  🟠 IMPORTANT — Fix before deploying to end users:")
    for _, desc in important_issues:
        print(f"     • {desc}")
    print()

if recommended_issues:
    print("  🟡 RECOMMENDED — Improves accuracy further:")
    for _, desc in recommended_issues:
        print(f"     • {desc}")
    print()

if not (critical_issues or important_issues or recommended_issues):
    print("  ✅ No issues detected — your model appears AI-ready!")

print()
print("=" * 68)
print("  📚 KEY RESOURCES")
print("=" * 68)
print("  Semantic Model Best Practices for Data Agent:")
print("    https://learn.microsoft.com/fabric/data-science/semantic-model-best-practices")
print("  Prep for AI — official documentation:")
print("    https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai")
print("  AI Data Schema setup:")
print("    https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-data-schema")
print("  AI Instructions:")
print("    https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-instructions")
print("  Verified Answers:")
print("    https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers")
print("  Fabric Toolbox — Data Agent Checklist & Utilities:")
print("    https://github.com/microsoft/fabric-toolbox/tree/main/samples/data_agent_checklist_notebooks")
print("  Semantic Link Labs:")
print("    https://github.com/microsoft/semantic-link-labs")
print("  Power BI Modeling MCP Server:")
print("    https://github.com/microsoft/powerbi-modeling-mcp")
print("=" * 68)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ### 📚 Learn More
# 
# | Resource | Link |
# |----------|------|
# | Semantic model best practices for data agent | [learn.microsoft.com](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices#prep-for-ai-make-semantic-model-ai-ready) |
# | Prepare your data for AI (Prep for AI) | [learn.microsoft.com](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-prepare-data-ai) |
# | Set an AI data schema | [learn.microsoft.com](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-prepare-data-ai-data-schema#set-an-ai-data-schema) |
# | AI Instructions | [learn.microsoft.com](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-prepare-data-ai-instructions) |
# | Verified Answers | [learn.microsoft.com](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-prepare-data-ai-verified-answers) |
# | Fabric Data Agent Checklist + Utilities notebook | [GitHub](https://github.com/microsoft/fabric-toolbox/tree/main/samples/data_agent_checklist_notebooks) |
# | Evaluate your data agent | [learn.microsoft.com](https://learn.microsoft.com/en-us/fabric/data-science/evaluate-data-agent) |
# | Semantic Link Labs | [GitHub](https://github.com/microsoft/semantic-link-labs) |
# | Power BI Modeling MCP Server | [GitHub](https://github.com/microsoft/powerbi-modeling-mcp) |
# 
# ---
# *You can safely delete this notebook after running it — it does not modify your semantic model.*

