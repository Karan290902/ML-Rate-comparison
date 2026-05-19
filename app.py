import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Commercial Comparison Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("Insurance Commercial Comparison Dashboard")

st.markdown("""
Compare insurers based on:
- Pricing competitiveness
- COA attractiveness
- Age-wise pricing
- Tenure-wise pricing
- Business suitability
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload Insurer Rate Cards",
    type=["xlsx", "csv"],
    accept_multiple_files=True
)

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if uploaded_files:

    all_data = []

    coa_inputs = {}

    st.sidebar.header("COA Inputs")

    # ---------------------------------------------------
    # PROCESS FILES
    # ---------------------------------------------------

    for uploaded_file in uploaded_files:

        insurer_name = uploaded_file.name.split(".")[0]

        # ---------------------------------------------------
        # COA INPUT
        # ---------------------------------------------------

        coa = st.sidebar.text_input(
            f"{insurer_name} COA %",
            value=""
        )

        try:
            coa = float(coa)
        except:
            coa = 0

        coa_inputs[insurer_name] = coa

        # ---------------------------------------------------
        # READ FILE
        # ---------------------------------------------------

        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # ---------------------------------------------------
        # VALIDATION
        # ---------------------------------------------------

        if 'Entry Age' not in df.columns:

            st.error(
                f"'Entry Age' missing in {uploaded_file.name}"
            )

            continue

        # ---------------------------------------------------
        # CONVERT TO LONG FORMAT
        # ---------------------------------------------------

        df_long = df.melt(
            id_vars=['Entry Age'],
            var_name='Tenure',
            value_name='Rate_Per_Lakh'
        )

        df_long.rename(
            columns={
                'Entry Age': 'Age'
            },
            inplace=True
        )

        # ---------------------------------------------------
        # ADD INSURER
        # ---------------------------------------------------

        df_long['Insurer'] = insurer_name

        df_long['COA'] = coa

        # ---------------------------------------------------
        # CLEAN DATA
        # ---------------------------------------------------

        df_long['Age'] = pd.to_numeric(
            df_long['Age'],
            errors='coerce'
        )

        df_long['Tenure'] = pd.to_numeric(
            df_long['Tenure'],
            errors='coerce'
        )

        df_long['Rate_Per_Lakh'] = pd.to_numeric(
            df_long['Rate_Per_Lakh'],
            errors='coerce'
        )

        df_long.dropna(inplace=True)

        all_data.append(df_long)

    # ---------------------------------------------------
    # FINAL DATAFRAME
    # ---------------------------------------------------

    if len(all_data) > 0:

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        # ---------------------------------------------------
        # FILTERS
        # ---------------------------------------------------

        st.sidebar.header("Filters")

        selected_age = st.sidebar.selectbox(
            "Select Age",
            sorted(final_df['Age'].unique())
        )

        selected_tenure = st.sidebar.selectbox(
            "Select Tenure",
            sorted(final_df['Tenure'].unique())
        )

        # ---------------------------------------------------
        # FILTER DATA
        # ---------------------------------------------------

        filtered_df = final_df[
            (final_df['Age'] == selected_age) &
            (final_df['Tenure'] == selected_tenure)
        ]

        filtered_df = filtered_df.sort_values(
            by='Rate_Per_Lakh'
        )

        # ---------------------------------------------------
        # BEST PRICING INSURER
        # ---------------------------------------------------

        st.subheader(
            f"Best Pricing | Age {selected_age} | Tenure {selected_tenure}"
        )

        if not filtered_df.empty:

            best_price = filtered_df.iloc[0]

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Lowest Price Insurer",
                best_price['Insurer']
            )

            col2.metric(
                "Rate Per Lakh",
                round(best_price['Rate_Per_Lakh'], 2)
            )

            col3.metric(
                "COA %",
                best_price['COA']
            )

        # ---------------------------------------------------
        # SIDE-BY-SIDE COMPARISON
        # ---------------------------------------------------

        st.subheader("Side-by-Side Rate Comparison")

        comparison_matrix = final_df.pivot_table(
            index=['Age', 'Tenure'],
            columns='Insurer',
            values='Rate_Per_Lakh'
        ).reset_index()

        insurer_cols = comparison_matrix.columns[2:]

        # ---------------------------------------------------
        # DIFFERENCE %
        # ---------------------------------------------------

        if len(insurer_cols) >= 2:

            base = insurer_cols[0]

            for insurer in insurer_cols[1:]:

                comparison_matrix[
                    f'{insurer} Difference %'
                ] = (
                    (
                        comparison_matrix[insurer] -
                        comparison_matrix[base]
                    )
                    /
                    comparison_matrix[base]
                ) * 100

                comparison_matrix[
                    f'{insurer} Difference %'
                ] = comparison_matrix[
                    f'{insurer} Difference %'
                ].round(2)

        st.dataframe(
            comparison_matrix,
            use_container_width=True
        )

        # ---------------------------------------------------
        # OVERALL ANALYSIS
        # ---------------------------------------------------

        st.subheader("Overall Insurer Analysis")

        overall = (
            final_df.groupby('Insurer')[
                'Rate_Per_Lakh'
            ]
            .mean()
            .reset_index()
        )

        overall['COA'] = overall['Insurer'].map(
            coa_inputs
        )

        overall = overall.sort_values(
            by='Rate_Per_Lakh'
        )

        st.dataframe(
            overall,
            use_container_width=True
        )

        # ---------------------------------------------------
        # BEST PRICING INSURER
        # ---------------------------------------------------

        best_pricing = overall.iloc[0]

        # ---------------------------------------------------
        # BEST COA INSURER
        # ---------------------------------------------------

        best_coa = overall.sort_values(
            by='COA',
            ascending=False
        ).iloc[0]

        # ---------------------------------------------------
        # BUSINESS INTERPRETATION
        # ---------------------------------------------------

        st.subheader("Business Interpretation")

        interpretation = ""

        for _, row in overall.iterrows():

            insurer = row['Insurer']
            rate = row['Rate_Per_Lakh']
            coa = row['COA']

            pricing_strength = ""

            if rate <= overall['Rate_Per_Lakh'].quantile(0.25):
                pricing_strength = "Excellent Pricing"

            elif rate <= overall['Rate_Per_Lakh'].median():
                pricing_strength = "Good Pricing"

            else:
                pricing_strength = "Higher Pricing"

            coa_strength = ""

            if coa >= overall['COA'].quantile(0.75):
                coa_strength = "Strong COA"

            elif coa >= overall['COA'].median():
                coa_strength = "Moderate COA"

            else:
                coa_strength = "Lower COA"

            recommendation = ""

            if pricing_strength == "Excellent Pricing" and coa_strength == "Strong COA":
                recommendation = "Excellent Commercial Proposition"

            elif pricing_strength == "Excellent Pricing":
                recommendation = "Best for Scale Business"

            elif coa_strength == "Strong COA":
                recommendation = "Best for Higher Revenue"

            else:
                recommendation = "Balanced Proposition"

            interpretation += f"""
### {insurer}

- Avg Rate Per Lakh: {round(rate,2)}
- COA: {coa}%

Pricing View:
- {pricing_strength}

COA View:
- {coa_strength}

Recommendation:
- {recommendation}

"""

        st.markdown(interpretation)

        # ---------------------------------------------------
        # FINAL RECOMMENDATION
        # ---------------------------------------------------

        st.subheader("Final Recommendation")

        final_text = f"""
### Best Pricing Insurer
{best_pricing['Insurer']}

Reason:
- Lowest overall pricing
- Better conversion potential
- Better scalability

### Best COA Insurer
{best_coa['Insurer']}

Reason:
- Higher acquisition economics
- Better broker revenue opportunity

### Suggested Decision Logic

- If focus is scale and customer acquisition:
  Prefer lower pricing insurer.

- If focus is higher margins/revenue:
  Prefer stronger COA insurer.

- Best insurer practically is the one where:
  pricing difference is manageable
  AND
  COA advantage is commercially meaningful.
"""

        st.info(final_text)

        # ---------------------------------------------------
        # AGE SLAB ANALYSIS
        # ---------------------------------------------------

        st.subheader("Best Pricing by Age Slab")

        bins = [18, 25, 35, 45, 55, 100]

        labels = [
            '18-25',
            '26-35',
            '36-45',
            '46-55',
            '56+'
        ]

        final_df['Age_Slab'] = pd.cut(
            final_df['Age'],
            bins=bins,
            labels=labels,
            right=True
        )

        slab = (
            final_df.groupby(
                ['Age_Slab', 'Insurer']
            )['Rate_Per_Lakh']
            .mean()
            .reset_index()
        )

        best_slab = (
            slab.loc[
                slab.groupby('Age_Slab')[
                    'Rate_Per_Lakh'
                ].idxmin()
            ]
        )

        st.dataframe(
            best_slab,
            use_container_width=True
        )

        # ---------------------------------------------------
        # AGE VS RATE GRAPH
        # ---------------------------------------------------

        st.subheader("Age vs Rate Comparison")

        selected_chart_tenure = st.selectbox(
            "Select Tenure",
            sorted(final_df['Tenure'].unique())
        )

        chart_df = final_df[
            final_df['Tenure'] == selected_chart_tenure
        ]

        fig_age = px.line(
            chart_df,
            x='Age',
            y='Rate_Per_Lakh',
            color='Insurer',
            markers=True,
            title=f'Age vs Rate | Tenure {selected_chart_tenure}'
        )

        st.plotly_chart(
            fig_age,
            use_container_width=True
        )

        # ---------------------------------------------------
        # TENURE VS RATE GRAPH
        # ---------------------------------------------------

        st.subheader("Tenure vs Rate Comparison")

        selected_chart_age = st.selectbox(
            "Select Age",
            sorted(final_df['Age'].unique()),
            key='tenure_chart'
        )

        tenure_chart_df = final_df[
            final_df['Age'] == selected_chart_age
        ]

        fig_tenure = px.line(
            tenure_chart_df,
            x='Tenure',
            y='Rate_Per_Lakh',
            color='Insurer',
            markers=True,
            title=f'Tenure vs Rate | Age {selected_chart_age}'
        )

        st.plotly_chart(
            fig_tenure,
            use_container_width=True
        )

        # ---------------------------------------------------
        # RAW DATA
        # ---------------------------------------------------

        if st.checkbox("Show Raw Data"):

            st.dataframe(
                final_df,
                use_container_width=True
            )

else:

    st.warning(
        "Please upload insurer files."
    )
