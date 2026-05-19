from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def extract_rate_blocks(uploaded_file, sheet_name: str = "LAP Reducing") -> pd.DataFrame:
    raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)

    records = []
    entry_age_cells = []

    for row_idx in raw.index:
        for col_idx in raw.columns:
            if clean_text(raw.iat[row_idx, col_idx]).lower() == "entry age":
                entry_age_cells.append((row_idx, col_idx))

    if not entry_age_cells:
        raise ValueError("No 'Entry Age' table found in the uploaded Excel file.")

    for header_row, start_col in entry_age_cells:
        insurer = clean_text(raw.iat[max(header_row - 2, 0), start_col])
        product = clean_text(raw.iat[max(header_row - 1, 0), start_col])

        if not insurer:
            insurer = f"Insurer {start_col}"

        if not product:
            product = sheet_name

        term_cols = []
        col = start_col + 1

        while col in raw.columns and pd.notna(raw.iat[header_row, col]):
            term_cols.append((col, int(raw.iat[header_row, col])))
            col += 1

        row = header_row + 1

        while row in raw.index and pd.notna(raw.iat[row, start_col]):
            age = int(raw.iat[row, start_col])

            for term_col, term in term_cols:
                premium_rate = raw.iat[row, term_col]

                if pd.notna(premium_rate):
                    records.append(
                        {
                            "insurer": insurer.upper(),
                            "product": product,
                            "age": age,
                            "term_years": term,
                            "premium_rate": float(premium_rate),
                        }
                    )

            row += 1

    data = pd.DataFrame(records)

    if data.empty:
        raise ValueError("No premium rates could be extracted.")

    return data.sort_values(["insurer", "age", "term_years"]).reset_index(drop=True)


def train_simple_model(data: pd.DataFrame):
    insurers = sorted(data["insurer"].unique())

    age = data["age"].to_numpy(dtype=float)
    term = data["term_years"].to_numpy(dtype=float)

    columns = [
        np.ones(len(data)),
        age,
        term,
        age ** 2,
        term ** 2,
        age * term,
    ]

    for insurer in insurers[1:]:
        columns.append((data["insurer"].to_numpy() == insurer).astype(float))

    x = np.column_stack(columns)
    y = np.log1p(data["premium_rate"].to_numpy(dtype=float))

    ridge = 1e-6 * np.eye(x.shape[1])
    coefficients = np.linalg.solve(x.T @ x + ridge, x.T @ y)

    return {
        "insurers": insurers,
        "coefficients": coefficients,
    }


def predict_rate(model, insurer: str, age: int, term_years: int) -> float:
    insurers = model["insurers"]
    coefficients = model["coefficients"]

    features = [
        1.0,
        age,
        term_years,
        age ** 2,
        term_years ** 2,
        age * term_years,
    ]

    for extra_insurer in insurers[1:]:
        features.append(1.0 if insurer == extra_insurer else 0.0)

    return float(np.expm1(np.array(features) @ coefficients))


def compare_premiums(
    data: pd.DataFrame,
    model,
    age: int,
    term_years: int,
    payment_mode: str,
    sum_assured: float,
    monthly_loading: float,
) -> pd.DataFrame:
    rows = []

    for insurer in sorted(data["insurer"].unique()):
        insurer_data = data[data["insurer"] == insurer]
        product = insurer_data["product"].iloc[0]

        exact = insurer_data[
            (insurer_data["age"] == age)
            & (insurer_data["term_years"] == term_years)
        ]

        if not exact.empty:
            rate_per_1000 = float(exact["premium_rate"].iloc[0])
            basis = "Exact table rate"
        elif insurer_data["age"].min() <= age <= insurer_data["age"].max():
            rate_per_1000 = predict_rate(model, insurer, age, term_years)
            basis = "ML estimate"
        else:
            continue

        yearly_premium = rate_per_1000 * (sum_assured / 1000)

        if payment_mode == "Monthly":
            premium = yearly_premium * monthly_loading / 12
        else:
            premium = yearly_premium

        rows.append(
            {
                "Insurer": insurer,
                "Product": product,
                "Age Range": f"{insurer_data['age'].min()}-{insurer_data['age'].max()}",
                "Term": term_years,
                "Rate per 1000": round(rate_per_1000, 2),
                "Payment Mode": payment_mode,
                "Premium": round(premium, 2),
                "Basis": basis,
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    return result.sort_values("Premium").reset_index(drop=True)


def main():
    st.set_page_config(
        page_title="Premium Rate Comparison",
        page_icon="📊",
        layout="wide",
    )

    st.title("Premium Rate Comparison")
    st.caption("Upload insurer premium rate Excel and compare premiums by age, term, and payment mode.")

    uploaded_file = st.file_uploader(
        "Upload premium rate Excel file",
        type=["xlsx"],
    )

    if uploaded_file is None:
        st.info("Upload the Excel file to start comparison.")
        return

    try:
        data = extract_rate_blocks(uploaded_file)
    except Exception as error:
        st.error(f"Could not read Excel file: {error}")
        return

    model = train_simple_model(data)

    min_age = int(data["age"].min())
    max_age = int(data["age"].max())
    terms = sorted(data["term_years"].unique())

    with st.sidebar:
        st.header("Quote Inputs")

        age = st.slider(
            "Entry Age",
            min_value=min_age,
            max_value=max_age,
            value=min_age,
        )

        term_years = st.selectbox(
            "Policy Term",
            options=terms,
        )

        payment_mode = st.radio(
            "Payment Mode",
            options=["Yearly", "Monthly"],
            horizontal=True,
        )

        sum_assured = st.number_input(
            "Sum Assured",
            min_value=100000,
            max_value=100000000,
            value=1000000,
            step=100000,
        )

        monthly_loading = st.number_input(
            "Monthly Loading Factor",
            min_value=1.0,
            max_value=1.5,
            value=1.0,
            step=0.01,
            help="Use 1.00 if monthly premium is yearly premium divided by 12.",
        )

    result = compare_premiums(
        data=data,
        model=model,
        age=age,
        term_years=int(term_years),
        payment_mode=payment_mode,
        sum_assured=float(sum_assured),
        monthly_loading=float(monthly_loading),
    )

    if result.empty:
        st.warning("No insurer data available for the selected age and term.")
        return

    cheapest = result.iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Lowest Insurer", cheapest["Insurer"])
    col2.metric("Lowest Premium", f"{cheapest['Premium']:,.2f}")
    col3.metric("Insurers Compared", len(result))

    st.subheader("Premium Comparison")
    st.dataframe(result, use_container_width=True, hide_index=True)

    st.subheader("Premium Chart")
    chart_data = result.set_index("Insurer")[["Premium"]]
    st.bar_chart(chart_data, use_container_width=True)

    st.download_button(
        label="Download Comparison CSV",
        data=result.to_csv(index=False).encode("utf-8"),
        file_name="premium_comparison.csv",
        mime="text/csv",
    )

    with st.expander("Data Coverage"):
        coverage = (
            data.groupby("insurer")
            .agg(
                min_age=("age", "min"),
                max_age=("age", "max"),
                min_term=("term_years", "min"),
                max_term=("term_years", "max"),
                records=("premium_rate", "count"),
            )
            .reset_index()
        )

        st.dataframe(coverage, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()