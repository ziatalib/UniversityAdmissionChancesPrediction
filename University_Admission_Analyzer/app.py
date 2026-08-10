"""
University Admission Analyzer
==============================
A Streamlit dashboard that helps a student estimate their admission chances
across different universities and programs, based on their academic marks
and historical closing-merit data.

Author: Generated for a Programming for AI university project.

Libraries used:
- pandas  -> reading, cleaning and analyzing the historical dataset
- numpy   -> numerical calculations (aggregate formula, statistics)
- matplotlib -> base charts
- seaborn    -> statistical, styled charts
- streamlit  -> the web dashboard itself
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# --------------------------------------------------------------------------
# GLOBAL CONFIG
# --------------------------------------------------------------------------

DATA_PATH = "admission_data.csv"

# The weighting formula used to calculate the student's aggregate.
# This mirrors the common Pakistani engineering-admission style formula
# (Matric 10%, Intermediate 40%, Entry Test 50%) but is clearly displayed
# to the user so it is never a "hidden" calculation.
WEIGHTS = {
    "matric": 0.10,
    "intermediate": 0.40,
    "entry_test": 0.50,
}

# Thresholds (in merit points) used to bucket a student's chances.
HIGH_CHANCE_THRESHOLD = 2.0     # aggregate >= closing_merit - 2  -> High
MODERATE_CHANCE_THRESHOLD = -5.0  # aggregate >= closing_merit - 5  -> Moderate, else Low

sns.set_theme(style="whitegrid")  # gives seaborn charts a clean academic look


# --------------------------------------------------------------------------
# DATA LOADING & CLEANING
# --------------------------------------------------------------------------

@st.cache_data
def load_and_clean_data(path: str):
    """
    Reads the CSV dataset, cleans it, and returns a tuple:
    (cleaned_dataframe, cleaning_report_dict)

    The cleaning report is shown to the user so the "Data Cleaning" step
    of the project is transparent rather than a hidden black box.
    """
    report = {
        "missing_file": False,
        "rows_before": 0,
        "missing_values_removed": 0,
        "duplicates_removed": 0,
        "invalid_rows_removed": 0,
        "rows_after": 0,
        "missing_columns": [],
    }

    if not os.path.exists(path):
        report["missing_file"] = True
        return pd.DataFrame(), report

    df = pd.read_csv(path)
    report["rows_before"] = len(df)

    # 1. Check required columns exist. If some are missing, we cannot safely
    #    continue, so we return an empty dataframe with a clear report.
    required_columns = ["University", "Program", "Year", "Closing_Merit",
                         "Total_Seats", "Applicants", "Admission_Status"]
    missing_cols = [c for c in required_columns if c not in df.columns]
    report["missing_columns"] = missing_cols
    if missing_cols:
        return pd.DataFrame(), report

    # 2. Convert numeric columns to actual numbers. Any value that cannot be
    #    converted (blank, text, etc.) becomes NaN so pandas can detect it.
    numeric_cols = ["Year", "Closing_Merit", "Total_Seats", "Applicants"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. Detect and remove rows with missing values in the columns we
    #    actually need for analysis.
    before_na = len(df)
    df = df.dropna(subset=["University", "Program", "Year", "Closing_Merit", "Total_Seats"])
    report["missing_values_removed"] = before_na - len(df)

    # 4. Remove duplicate rows (same university+program+year repeated).
    before_dup = len(df)
    df = df.drop_duplicates(subset=["University", "Program", "Year"], keep="first")
    report["duplicates_removed"] = before_dup - len(df)

    # 5. Validate numerical ranges. A percentage/merit value must realistically
    #    be between 0 and 100. Seats and applicants must be positive.
    before_invalid = len(df)
    df = df[(df["Closing_Merit"] > 0) & (df["Closing_Merit"] <= 100)]
    df = df[df["Total_Seats"] > 0]
    df = df[df["Applicants"].fillna(0) >= 0]
    report["invalid_rows_removed"] = before_invalid - len(df)

    df = df.reset_index(drop=True)
    report["rows_after"] = len(df)
    return df, report


# --------------------------------------------------------------------------
# AGGREGATE CALCULATION
# --------------------------------------------------------------------------

def calculate_aggregate(matric_pct: float, inter_pct: float, test_pct: float) -> float:
    """
    Calculates the student's final aggregate using the weighting system
    defined in WEIGHTS. Uses NumPy for the weighted-sum calculation.
    """
    marks = np.array([matric_pct, inter_pct, test_pct])
    weights = np.array([WEIGHTS["matric"], WEIGHTS["intermediate"], WEIGHTS["entry_test"]])
    aggregate = float(np.dot(marks, weights))
    return round(aggregate, 2)


def validate_percentage(value: float, field_name: str) -> list:
    """
    Returns a list of error strings if the given percentage is invalid.
    An empty list means the value is valid.
    """
    errors = []
    if value is None:
        errors.append(f"{field_name} is required.")
        return errors
    if value < 0 or value > 100:
        errors.append(f"{field_name} must be between 0 and 100.")
    return errors


# --------------------------------------------------------------------------
# ADMISSION CHANCE ANALYSIS
# --------------------------------------------------------------------------

def classify_chance(difference: float) -> str:
    """
    Classifies admission chance based on the difference between the
    student's aggregate and a program's closing merit.
    difference = student_aggregate - closing_merit
    """
    if difference >= HIGH_CHANCE_THRESHOLD:
        return "High Chance"
    elif difference >= MODERATE_CHANCE_THRESHOLD:
        return "Moderate Chance"
    else:
        return "Low Chance"


def build_chance_table(df: pd.DataFrame, student_aggregate: float) -> pd.DataFrame:
    """
    Builds the university/program comparison table with the student's
    estimated admission chance for every row in the (already filtered)
    dataset. Uses the most recent year available per university+program
    so the comparison reflects the latest known closing merit.
    """
    if df.empty:
        return pd.DataFrame()

    # Keep only the latest year per University+Program combination.
    latest = (
        df.sort_values("Year")
        .groupby(["University", "Program"], as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    latest["Student_Aggregate"] = student_aggregate
    latest["Difference"] = np.round(student_aggregate - latest["Closing_Merit"], 2)
    latest["Estimated_Chance"] = latest["Difference"].apply(classify_chance)

    result = latest[["University", "Program", "Year", "Closing_Merit",
                      "Student_Aggregate", "Difference", "Estimated_Chance"]]
    result = result.sort_values("Difference", ascending=False).reset_index(drop=True)
    return result


# --------------------------------------------------------------------------
# RECOMMENDATIONS
# --------------------------------------------------------------------------

def generate_recommendations(chance_table: pd.DataFrame) -> dict:
    """
    Splits the chance table into Best / Moderate / Backup option groups,
    each sorted so the most favorable options appear first.
    """
    if chance_table.empty:
        return {"best": pd.DataFrame(), "moderate": pd.DataFrame(), "backup": pd.DataFrame()}

    best = chance_table[chance_table["Estimated_Chance"] == "High Chance"].sort_values(
        "Difference", ascending=False
    )
    moderate = chance_table[chance_table["Estimated_Chance"] == "Moderate Chance"].sort_values(
        "Difference", ascending=False
    )
    backup = chance_table[chance_table["Estimated_Chance"] == "Low Chance"].sort_values(
        "Difference", ascending=False
    )
    return {"best": best, "moderate": moderate, "backup": backup}


# --------------------------------------------------------------------------
# DATA ANALYSIS / STATISTICS
# --------------------------------------------------------------------------

def compute_statistics(df: pd.DataFrame) -> dict:
    """
    Computes summary statistics over the (filtered) dataset using
    NumPy/Pandas aggregation functions.
    """
    if df.empty:
        return {}

    avg_merit = float(np.mean(df["Closing_Merit"]))
    max_merit_row = df.loc[df["Closing_Merit"].idxmax()]
    min_merit_row = df.loc[df["Closing_Merit"].idxmin()]

    # "Most competitive" = highest average closing merit per program.
    program_avg = df.groupby("Program")["Closing_Merit"].mean().sort_values(ascending=False)
    most_competitive_program = program_avg.index[0] if not program_avg.empty else "N/A"
    most_accessible_program = program_avg.index[-1] if not program_avg.empty else "N/A"

    stats = {
        "average_closing_merit": round(avg_merit, 2),
        "highest_closing_merit": round(float(max_merit_row["Closing_Merit"]), 2),
        "highest_merit_program": f"{max_merit_row['Program']} @ {max_merit_row['University']}",
        "lowest_closing_merit": round(float(min_merit_row["Closing_Merit"]), 2),
        "lowest_merit_program": f"{min_merit_row['Program']} @ {min_merit_row['University']}",
        "most_competitive_program": most_competitive_program,
        "most_accessible_program": most_accessible_program,
        "num_records": len(df),
        "num_universities": df["University"].nunique(),
        "num_programs": df["Program"].nunique(),
    }
    return stats


# --------------------------------------------------------------------------
# VISUALIZATIONS
# --------------------------------------------------------------------------

def chart_university_avg_merit(df: pd.DataFrame):
    """Matplotlib bar chart: average closing merit per university."""
    avg_by_uni = df.groupby("University")["Closing_Merit"].mean().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(avg_by_uni.index, avg_by_uni.values, color="#2E86AB")
    ax.set_xlabel("Average Closing Merit (%)")
    ax.set_ylabel("University")
    ax.set_title("University-wise Average Closing Merit")
    for i, v in enumerate(avg_by_uni.values):
        ax.text(v + 0.3, i, f"{v:.1f}", va="center", fontsize=8)
    fig.tight_layout()
    return fig


def chart_program_avg_merit(df: pd.DataFrame):
    """Seaborn bar chart: average closing merit per program."""
    avg_by_prog = df.groupby("Program")["Closing_Merit"].mean().sort_values(ascending=False).reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=avg_by_prog, x="Closing_Merit", y="Program", hue="Program",
                palette="viridis", ax=ax, legend=False)
    ax.set_xlabel("Average Closing Merit (%)")
    ax.set_ylabel("Program")
    ax.set_title("Program-wise Average Closing Merit")
    fig.tight_layout()
    return fig


def chart_student_vs_merit(chance_table: pd.DataFrame):
    """Matplotlib scatter/line comparing student aggregate to each program's closing merit."""
    if chance_table.empty:
        return None

    subset = chance_table.head(15)  # keep it readable
    fig, ax = plt.subplots(figsize=(9, 5))
    labels = [f"{row.Program}\n({row.University[:18]}...)" if len(row.University) > 18
              else f"{row.Program}\n({row.University})" for row in subset.itertuples()]
    x = np.arange(len(subset))

    ax.plot(x, subset["Closing_Merit"], marker="o", label="Closing Merit", color="#E63946")
    ax.axhline(y=subset["Student_Aggregate"].iloc[0], color="#2A9D8F",
               linestyle="--", label="Student Aggregate")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("Percentage")
    ax.set_title("Student Aggregate vs. Program Closing Merit")
    ax.legend()
    fig.tight_layout()
    return fig


def chart_merit_distribution(df: pd.DataFrame):
    """Seaborn histogram/KDE showing the distribution of closing merits."""
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df["Closing_Merit"], kde=True, color="#6A4C93", ax=ax, bins=15)
    ax.set_xlabel("Closing Merit (%)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Closing Merits Across Programs")
    fig.tight_layout()
    return fig


def chart_competitiveness_heatmap(df: pd.DataFrame):
    """Seaborn heatmap: average closing merit by University x Program."""
    pivot = df.pivot_table(index="University", columns="Program",
                            values="Closing_Merit", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlOrRd", linewidths=0.5, ax=ax)
    ax.set_title("University vs. Program Competitiveness (Avg. Closing Merit)")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# STREAMLIT APP LAYOUT
# --------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="University Admission Analyzer",
        page_icon="🎓",
        layout="wide",
    )

    # ---- Simple academic-themed styling ----
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1B3A57;
            margin-bottom: 0;
        }
        .sub-header {
            color: #557A95;
            font-size: 1.05rem;
            margin-top: 0;
        }
        .disclaimer-box {
            background-color: #FFF3CD;
            border-left: 5px solid #FFC107;
            padding: 0.8rem 1rem;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-header">🎓 University Admission Analyzer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Estimate your admission chances across universities using historical closing-merit data.</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="disclaimer-box">⚠️ This tool provides an <b>estimated</b> admission chance based on '
        'historical/demo merit data. It is <b>not</b> a guarantee of admission and does not represent '
        'official university figures.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    # ---- 1. Load & clean data (with error handling for a missing file) ----
    df, report = load_and_clean_data(DATA_PATH)

    if report["missing_file"]:
        st.error(f"Dataset not found at '{DATA_PATH}'. Please make sure the CSV file is in the project folder.")
        st.stop()

    if report["missing_columns"]:
        st.error(f"The dataset is missing required columns: {', '.join(report['missing_columns'])}")
        st.stop()

    if df.empty:
        st.error("The dataset became empty after cleaning. Please check the CSV file for valid data.")
        st.stop()

    # ==========================================================
    # SIDEBAR — Student Input + Filters
    # ==========================================================
    with st.sidebar:
        st.header("👤 Student Profile")

        student_name = st.text_input("Student Name", placeholder="e.g. Ahmed Khan")

        matric_pct = st.number_input("Matric Percentage (%)", min_value=0.0, max_value=100.0,
                                      value=85.0, step=0.1)
        inter_pct = st.number_input("Intermediate Percentage (%)", min_value=0.0, max_value=100.0,
                                     value=80.0, step=0.1)
        test_pct = st.number_input("Entry Test Percentage (%)", min_value=0.0, max_value=100.0,
                                    value=75.0, step=0.1)

        st.markdown("---")
        st.header("🔎 Filters")

        all_universities = sorted(df["University"].unique().tolist())
        all_programs = sorted(df["Program"].unique().tolist())

        selected_universities = st.multiselect("Preferred Universities", all_universities,
                                                 default=all_universities)
        selected_programs = st.multiselect("Preferred Programs", all_programs,
                                            default=all_programs)

        analyze_clicked = st.button("📊 Analyze Admission Chances", type="primary", use_container_width=True)

    # ---- Input validation ----
    errors = []
    errors += validate_percentage(matric_pct, "Matric percentage")
    errors += validate_percentage(inter_pct, "Intermediate percentage")
    errors += validate_percentage(test_pct, "Entry test percentage")
    if not student_name.strip():
        errors.append("Student name cannot be empty.")
    if not selected_universities:
        errors.append("Please select at least one university.")
    if not selected_programs:
        errors.append("Please select at least one program.")

    if errors:
        st.warning("Please fix the following before continuing:")
        for e in errors:
            st.write(f"- {e}")
        st.stop()

    # Filter dataset according to sidebar selections. Handle the edge case
    # where a filter combination returns zero rows (division-by-zero safe).
    filtered_df = df[df["University"].isin(selected_universities) & df["Program"].isin(selected_programs)]
    if filtered_df.empty:
        st.error("No data matches the selected university/program filters. Try widening your selection.")
        st.stop()

    # ==========================================================
    # SECTION 2 — Student Profile & Aggregate
    # ==========================================================
    st.header("🧾 Student Profile & Aggregate Analysis")

    aggregate = calculate_aggregate(matric_pct, inter_pct, test_pct)

    st.markdown(
        f"**Aggregate Formula Used:** "
        f"`Aggregate = (Matric × {WEIGHTS['matric']*100:.0f}%) + "
        f"(Intermediate × {WEIGHTS['intermediate']*100:.0f}%) + "
        f"(Entry Test × {WEIGHTS['entry_test']*100:.0f}%)`"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Matric %", f"{matric_pct:.2f}%")
    c2.metric("Intermediate %", f"{inter_pct:.2f}%")
    c3.metric("Entry Test %", f"{test_pct:.2f}%")
    c4.metric("Final Aggregate", f"{aggregate:.2f}%")

    st.divider()

    # ==========================================================
    # SECTION 3 — Admission Chance Analysis + University Comparison
    # ==========================================================
    st.header("🎯 Admission Chances & University Comparison")

    chance_table = build_chance_table(filtered_df, aggregate)

    def highlight_chance(val):
        if val == "High Chance":
            return "background-color: #D4EDDA; color: #155724;"
        elif val == "Moderate Chance":
            return "background-color: #FFF3CD; color: #856404;"
        elif val == "Low Chance":
            return "background-color: #F8D7DA; color: #721C24;"
        return ""

    styled = chance_table.style.map(highlight_chance, subset=["Estimated_Chance"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.caption("Estimated chance based on the difference between your aggregate and each program's most recent closing merit. Not an official admission guarantee.")

    st.divider()

    # ==========================================================
    # SECTION 4 — Recommendations
    # ==========================================================
    st.header("💡 Recommended Programs")

    recs = generate_recommendations(chance_table)

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.subheader("✅ Best Options")
        if recs["best"].empty:
            st.info("No high-chance options found with current filters.")
        else:
            st.dataframe(recs["best"][["University", "Program", "Difference"]],
                         hide_index=True, use_container_width=True)
    with rc2:
        st.subheader("🟡 Moderate Options")
        if recs["moderate"].empty:
            st.info("No moderate-chance options found.")
        else:
            st.dataframe(recs["moderate"][["University", "Program", "Difference"]],
                         hide_index=True, use_container_width=True)
    with rc3:
        st.subheader("🛟 Backup Options")
        if recs["backup"].empty:
            st.info("No backup options found.")
        else:
            st.dataframe(recs["backup"][["University", "Program", "Difference"]],
                         hide_index=True, use_container_width=True)

    st.divider()

    # ==========================================================
    # SECTION 5 — Data Insights (statistics)
    # ==========================================================
    st.header("📈 Data Insights")

    stats = compute_statistics(filtered_df)

    s1, s2, s3 = st.columns(3)
    s1.metric("Average Closing Merit", f"{stats['average_closing_merit']}%")
    s2.metric("Highest Closing Merit", f"{stats['highest_closing_merit']}%")
    s3.metric("Lowest Closing Merit", f"{stats['lowest_closing_merit']}%")

    s4, s5, s6 = st.columns(3)
    s4.metric("Most Competitive Program", stats["most_competitive_program"])
    s5.metric("Most Accessible Program", stats["most_accessible_program"])
    s6.metric("Records Analyzed", stats["num_records"])

    st.caption(f"Data covers {stats['num_universities']} universities and {stats['num_programs']} programs "
               f"(after cleaning).")

    st.divider()

    # ==========================================================
    # SECTION 6 — Visualizations
    # ==========================================================
    st.header("📊 Visual Analysis")

    v1, v2 = st.columns(2)
    with v1:
        st.pyplot(chart_university_avg_merit(filtered_df))
    with v2:
        st.pyplot(chart_program_avg_merit(filtered_df))

    v3, v4 = st.columns(2)
    with v3:
        fig = chart_student_vs_merit(chance_table)
        if fig:
            st.pyplot(fig)
    with v4:
        st.pyplot(chart_merit_distribution(filtered_df))

    st.pyplot(chart_competitiveness_heatmap(filtered_df))

    st.divider()

    # ==========================================================
    # SECTION 7 — Data Cleaning Report (transparency)
    # ==========================================================
    with st.expander("🧹 Data Cleaning Report"):
        st.write(f"- Rows before cleaning: **{report['rows_before']}**")
        st.write(f"- Rows removed (missing values): **{report['missing_values_removed']}**")
        st.write(f"- Rows removed (duplicates): **{report['duplicates_removed']}**")
        st.write(f"- Rows removed (invalid values, e.g. merit > 100): **{report['invalid_rows_removed']}**")
        st.write(f"- Rows after cleaning: **{report['rows_after']}**")

    st.caption("Built with Python, Pandas, NumPy, Matplotlib, Seaborn and Streamlit. "
               "All charts and tables are generated dynamically from the dataset and your input.")


if __name__ == "__main__":
    main()
