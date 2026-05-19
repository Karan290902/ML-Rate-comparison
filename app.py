import streamlit as st
import pandas as pd
from io import BytesIO

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Insurance Premium Engine",
    layout="wide"
)

st.title("Insurance Premium Engine")

# ---------------------------------------------------
# MODE SELECTION
# ---------------------------------------------------

mode = st.sidebar.radio(
    "Select Mode",
    [
        "Insurer Comparison",
        "Bulk Premium Calculator"
    ]
)

# ===================================================
# MODE 1 : INSURER COMPARISON
# ===================================================

if mode == "Insurer Comparison":

    st.header("Insurer Comparison")

    uploaded_files = st.file_uploader(
        "Upload Insurer Rate Cards",
        type=["xlsx", "csv"],
        accept_multiple_files=True
    )

    if uploaded_files:

        all_data = []

        coa_inputs = {}

        st.sidebar.header("COA Inputs")

        # ---------------------------------------------------
        # PROCESS FILES
        # ---------------------------------------------------

        for uploaded_file in uploaded_files:

            insurer_name = uploaded_file.name.split(".")[0]

            coa = st.sidebar.number_input(
                f"{insurer_name} COA %",
                min_value=0.0,
                value=0.0
            )

            coa_inputs[insurer_name] = coa

            # Read file
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Convert
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

            df_long['Insurer'] = insurer_name

            df_long['COA'] = coa

            # Clean
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

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        # ---------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------

        st.subheader("Overall Insurer Summary")

        summary = (
            final_df.groupby('Insurer')[
                'Rate_Per_Lakh'
            ]
            .mean()
            .reset_index()
        )

        summary['COA'] = summary['Insurer'].map(
            coa_inputs
        )

        st.dataframe(
            summary,
            use_container_width=True
        )

        # ---------------------------------------------------
        # CHEAPEST FREQUENCY
        # ---------------------------------------------------

        st.subheader("Cheapest Insurer Frequency")

        cheapest_cases = (
            final_df.loc[
                final_df.groupby(
                    ['Age', 'Tenure']
                )['Rate_Per_Lakh'].idxmin()
            ]
        )

        frequency = (
            cheapest_cases['Insurer']
            .value_counts()
            .reset_index()
        )

        frequency.columns = [
            'Insurer',
            'Cheapest Cases'
        ]

        frequency['Cheapest %'] = (
            frequency['Cheapest Cases']
            /
            frequency['Cheapest Cases'].sum()
        ) * 100

        frequency['Cheapest %'] = (
            frequency['Cheapest %']
            .round(2)
        )

        st.dataframe(
            frequency,
            use_container_width=True
        )

# ===================================================
# MODE 2 : BULK PREMIUM CALCULATOR
# ===================================================

elif mode == "Bulk Premium Calculator":

    st.header("Bulk Premium Calculator")

    # ---------------------------------------------------
    # LOT FILE
    # ---------------------------------------------------

    lot_file = st.file_uploader(
        "Upload Lot File",
        type=["xlsx", "csv"]
    )

    # ---------------------------------------------------
    # RATE CARDS
    # ---------------------------------------------------

    insurer_files = st.file_uploader(
        "Upload Insurer Rate Cards",
        type=["xlsx", "csv"],
        accept_multiple_files=True
    )

    if lot_file and insurer_files:

        # ---------------------------------------------------
        # READ LOT FILE
        # ---------------------------------------------------

        if lot_file.name.endswith(".csv"):
            lot_df = pd.read_csv(lot_file)
        else:
            lot_df = pd.read_excel(lot_file)

        required_cols = [
            'Name',
            'Age',
            'Loan Amount',
            'Tenure'
        ]

        missing = [
            col for col in required_cols
            if col not in lot_df.columns
        ]

        if missing:

            st.error(
                f"Missing columns in lot file: {missing}"
            )

        else:

            # ---------------------------------------------------
            # PROCESS INSURERS
            # ---------------------------------------------------

            result_df = lot_df.copy()

            summary_data = []

            for insurer_file in insurer_files:

                insurer_name = insurer_file.name.split(".")[0]

                # Read insurer file
                if insurer_file.name.endswith(".csv"):
                    rate_df = pd.read_csv(insurer_file)
                else:
                    rate_df = pd.read_excel(insurer_file)

                # Convert age column
                rate_df['Entry Age'] = pd.to_numeric(
                    rate_df['Entry Age'],
                    errors='coerce'
                )

                # Premium list
                premiums = []

                for _, row in lot_df.iterrows():

                    age = row['Age']
                    tenure = row['Tenure']
                    loan_amount = row['Loan Amount']

                    premium = None

                    try:

                        rate = rate_df.loc[
                            rate_df['Entry Age'] == age,
                            str(tenure)
                        ].values[0]

                        premium = (
                            loan_amount / 100000
                        ) * rate

                    except:

                        premium = None

                    premiums.append(premium)

                # Add insurer premium
                result_df[
                    f'{insurer_name} Premium'
                ] = premiums

                # Portfolio summary
                total_premium = pd.Series(
                    premiums
                ).sum()

                summary_data.append({
                    'Insurer': insurer_name,
                    'Total Premium': round(
                        total_premium,
                        2
                    )
                })

            # ---------------------------------------------------
            # CHEAPEST INSURER
            # ---------------------------------------------------

            premium_cols = [
                col for col in result_df.columns
                if 'Premium' in col
            ]

            result_df['Cheapest Insurer'] = (
                result_df[premium_cols]
                .idxmin(axis=1)
                .str.replace(
                    ' Premium',
                    ''
                )
            )

            # ---------------------------------------------------
            # OUTPUT
            # ---------------------------------------------------

            st.subheader("Premium Calculation Output")

            st.dataframe(
                result_df,
                use_container_width=True
            )

            # ---------------------------------------------------
            # PORTFOLIO SUMMARY
            # ---------------------------------------------------

            st.subheader("Portfolio Summary")

            summary_df = pd.DataFrame(
                summary_data
            )

            st.dataframe(
                summary_df,
                use_container_width=True
            )

            # ---------------------------------------------------
            # EXPORT
            # ---------------------------------------------------

            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine='openpyxl'
            ) as writer:

                result_df.to_excel(
                    writer,
                    index=False,
                    sheet_name='Premium Output'
                )

                summary_df.to_excel(
                    writer,
                    index=False,
                    sheet_name='Portfolio Summary'
                )

            st.download_button(
                label="Download Premium Report",
                data=output.getvalue(),
                file_name="premium_calculation_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
