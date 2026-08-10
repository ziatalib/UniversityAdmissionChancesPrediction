# 🎓 University Admission Analyzer

A Streamlit dashboard that helps a student estimate their admission chances across
different universities and programs, based on their academic marks and historical
closing-merit data.

> ⚠️ **Disclaimer:** This project uses a realistic **sample/demo dataset**, not official
> university admission data. All admission chances shown are **estimates** based on
> historical patterns, not guarantees.

---

## 1. Project Structure

```
University_Admission_Analyzer/
│
├── app.py                 # Main Streamlit application
├── admission_data.csv     # Sample historical admission dataset
├── requirements.txt       # Python dependencies
├── README.md               # This file
└── assets/                 # (Reserved for extra assets, e.g. logo/screenshots)
```

---

## 2. Installing Dependencies (VS Code)

1. **Install Python 3.9+** if you don't already have it (check with `python --version`).
2. **Open the project folder in VS Code**: `File > Open Folder... > University_Admission_Analyzer`.
3. **(Recommended) Create a virtual environment**, so dependencies stay isolated:

   ```bash
   python -m venv venv
   ```

   Activate it:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **Install the required packages**:

   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Running the Project in VS Code

1. Open a terminal in VS Code (`` Ctrl+` `` or `Terminal > New Terminal`).
2. Make sure you're inside the `University_Admission_Analyzer` folder and your
   virtual environment (if used) is activated.
3. Run:

   ```bash
   streamlit run app.py
   ```

4. Streamlit will start a local server and automatically open the dashboard in your
   browser (usually at `http://localhost:8501`). If it doesn't open automatically,
   click the link shown in the terminal.
5. To stop the app, go back to the terminal and press `Ctrl+C`.

---

## 4. How the Application Works (Architecture)

The app follows a simple, linear flow, all inside `app.py`, organized into clearly
separated functions rather than one large script:

1. **Load & Clean Data** — `load_and_clean_data()` reads `admission_data.csv`,
   converts columns to proper numeric types, removes missing values, duplicates,
   and invalid rows (e.g. merit > 100%), and returns both the cleaned dataset and
   a "cleaning report" so the user can see exactly what was fixed.
2. **Collect Student Input** — the Streamlit sidebar collects the student's name,
   marks, and filter preferences (universities/programs), with validation.
3. **Calculate Aggregate** — `calculate_aggregate()` applies the weighted formula
   (Matric 10% + Intermediate 40% + Entry Test 50%) using NumPy.
4. **Build Comparison Table** — `build_chance_table()` compares the student's
   aggregate against each program's most recent closing merit and classifies the
   difference into High / Moderate / Low Chance using `classify_chance()`.
5. **Generate Recommendations** — `generate_recommendations()` splits the
   comparison table into Best / Moderate / Backup groups.
6. **Compute Statistics** — `compute_statistics()` calculates averages, extremes,
   and most/least competitive programs using Pandas/NumPy aggregation.
7. **Visualize** — five chart functions (Matplotlib + Seaborn) render the analysis.
8. **Render Dashboard** — `main()` ties everything together into a sectioned,
   styled Streamlit layout (sidebar inputs → profile → chances → recommendations
   → insights → charts → cleaning report).

---

## 5. Explanation of Every Major Function

| Function | Purpose |
|---|---|
| `load_and_clean_data(path)` | Reads the CSV, validates required columns exist, converts numeric columns, removes missing/duplicate/invalid rows, and returns the cleaned DataFrame plus a report of what was removed. |
| `calculate_aggregate(matric, inter, test)` | Computes the student's weighted aggregate percentage using NumPy's dot product over the marks and the defined weights. |
| `validate_percentage(value, field_name)` | Checks that a percentage value is present and between 0–100; returns a list of error messages (empty if valid). |
| `classify_chance(difference)` | Converts a numeric "aggregate − closing merit" difference into a "High / Moderate / Low Chance" label using fixed thresholds. |
| `build_chance_table(df, student_aggregate)` | Keeps the latest year per University+Program, then computes the difference and estimated chance for every row, producing the main comparison table. |
| `generate_recommendations(chance_table)` | Splits the comparison table into three DataFrames — Best, Moderate, and Backup options — each sorted by how favorable the difference is. |
| `compute_statistics(df)` | Uses Pandas groupby/aggregate and NumPy mean/max/min to compute average, highest, lowest closing merit, and the most competitive/accessible programs. |
| `chart_university_avg_merit(df)` | Matplotlib horizontal bar chart of average closing merit per university. |
| `chart_program_avg_merit(df)` | Seaborn bar chart of average closing merit per program. |
| `chart_student_vs_merit(chance_table)` | Matplotlib line/marker chart comparing the student's aggregate against multiple programs' closing merits. |
| `chart_merit_distribution(df)` | Seaborn histogram + KDE showing how closing merits are distributed across all programs. |
| `chart_competitiveness_heatmap(df)` | Seaborn heatmap of average closing merit across University × Program combinations. |
| `main()` | Configures the page, applies custom CSS styling, and lays out the full dashboard: sidebar inputs, validation, and all seven main sections. |

---

## 6. Where Each Library Is Used

- **NumPy** — `calculate_aggregate()` (weighted dot-product calculation), `build_chance_table()`
  (vectorized difference calculation), and `compute_statistics()` (mean/max/min aggregation).
- **Pandas** — `load_and_clean_data()` (reading CSV, type conversion, `dropna`,
  `drop_duplicates`, filtering), `build_chance_table()` (`groupby`, `sort_values`, `tail`),
  and `compute_statistics()` (`groupby`, `mean`, `idxmax`/`idxmin`, `nunique`).
- **Matplotlib** — `chart_university_avg_merit()` and `chart_student_vs_merit()` build
  raw `fig, ax = plt.subplots()` charts with custom labels, titles, and legends.
- **Seaborn** — `chart_program_avg_merit()`, `chart_merit_distribution()`, and
  `chart_competitiveness_heatmap()` use `sns.barplot`, `sns.histplot`, and `sns.heatmap`
  for styled statistical visualizations.
- **Streamlit** — the entire `main()` function: sidebar widgets (`st.number_input`,
  `st.multiselect`, `st.text_input`, `st.button`), layout (`st.columns`, `st.expander`,
  `st.divider`), metrics (`st.metric`), styled tables (`st.dataframe` with `.style.map`),
  and rendering charts (`st.pyplot`).

---

## 7. Error Handling Covered

- **Missing dataset file** — shows a friendly error and stops instead of crashing.
- **Missing required columns** — detected and reported by name.
- **Invalid marks** (outside 0–100, or empty) — caught by `validate_percentage()`
  before any calculation happens.
- **Empty student name** — blocked with a clear message.
- **Invalid CSV values** (e.g. merit of `150`, blank cells) — coerced to `NaN` and
  removed during cleaning, with counts shown in the "Data Cleaning Report".
- **Division by zero** — the app never divides by a value that can be zero without
  first filtering it out (e.g. `Total_Seats > 0` is enforced during cleaning).
- **Empty filter results** — if a university/program filter combination returns no
  rows, the user is warned instead of the app crashing on an empty DataFrame.

---

## 8. Sample Dataset Notes

`admission_data.csv` is a **realistic but clearly synthetic/demo dataset** covering
25 universities × up to 12 programs × 10 years (2015–2024), with closing merit,
seat counts, and applicant numbers — over **2,600 rows** in total (around 2,550
after cleaning). A small, proportional number of rows were intentionally left with
missing values, duplicates, and out-of-range merit values so the data-cleaning logic
in `app.py` has genuine, visible work to do — this is **not official admission data**.

---

## 9. Fifteen Likely Presentation / Viva Questions & Answers

1. **Q: What does this project do?**
   A: It lets a student enter their academic marks, calculates a weighted aggregate,
   and compares it against historical closing merits to estimate admission chances
   across universities and programs.

2. **Q: Why is the aggregate formula weighted the way it is (10/40/50)?**
   A: It mirrors a common real-world admission formula style (heavier weight on the
   entry test), and is clearly displayed in the app so the calculation isn't hidden.

3. **Q: How is the "admission chance" decided?**
   A: By subtracting the closing merit from the student's aggregate. A difference
   at or above +2 is "High Chance", down to -5 is "Moderate", and below that is
   "Low Chance" — thresholds defined as constants in the code.

4. **Q: Why do you use the *latest year* of data per university/program?**
   A: Closing merits change year to year, so the most recent year is the most
   relevant reference point for estimating current chances.

5. **Q: Where exactly is NumPy used, and why not just Python math?**
   A: In `calculate_aggregate()` (weighted dot product) and in statistics
   (mean/max/min). NumPy makes vectorized numeric operations concise and is a
   required project technology.

6. **Q: What does the data-cleaning step actually remove?**
   A: Rows with missing values in key columns, exact duplicate university/program/
   year entries, and rows with invalid numeric values (e.g. merit above 100%).

7. **Q: How does the app handle a missing CSV file?**
   A: `load_and_clean_data()` checks `os.path.exists()` first and the app shows a
   friendly `st.error()` message and stops, instead of crashing with a traceback.

8. **Q: What happens if a student enters marks above 100%?**
   A: `validate_percentage()` catches it and the app shows a warning listing the
   exact problem before any calculation is attempted.

9. **Q: Why did you separate the code into functions instead of one script?**
   A: For readability, reusability, and easier testing/debugging — each function
   has a single clear responsibility (cleaning, calculation, charting, etc.).

10. **Q: What's the difference between Matplotlib and Seaborn usage here?**
    A: Matplotlib is used for custom bar/line charts needing manual control (e.g.
    labeled bars, dual-series comparison); Seaborn is used for statistical charts
    like the heatmap and distribution plot, where its built-in styling is faster.

11. **Q: How would you extend this project with machine learning?**
    A: You could train a classifier (e.g. logistic regression) on historical
    admitted/rejected outcomes to predict probability of admission — but this
    project intentionally sticks to transparent statistical analysis instead,
    since the data doesn't include real applicant-level outcomes.

12. **Q: Why is "Applicants" cleaned differently from "Closing_Merit"?**
    A: `Closing_Merit` and `Total_Seats` are required for chance calculations
    and are strictly validated (must be > 0 and ≤ 100 for merit). `Applicants`
    is informational, so missing values are treated as 0 rather than dropping
    the whole row.

13. **Q: What is `st.cache_data` doing in `load_and_clean_data`?**
    A: It caches the cleaned DataFrame so the CSV isn't re-read and re-cleaned on
    every single user interaction, which keeps the dashboard responsive.

14. **Q: How do you avoid a division-by-zero error in this project?**
    A: Rows with `Total_Seats <= 0` are filtered out during cleaning, so no later
    calculation (e.g. seat-utilization ratios) can divide by zero.

15. **Q: Is this tool giving official admission guarantees?**
    A: No — the dashboard explicitly labels all results as "estimated" and
    displays a disclaimer banner stating the data is historical/demo data, not
    an official or guaranteed outcome.
