import pandas as pd
import plotly.express as px
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Sales Insight & Dynamic Target Dashboard", layout="wide"
)

st.title("📊 Monthly Sales Insight & Dynamic MPO Target Dashboard")
st.markdown(
    "Upload your monthly sales data to analyze performance and generate"
    " dynamic, individualized MPO targets."
)

# --- 1. FILE UPLOAD BACKEND ---
uploaded_file = st.file_uploader(
    "Upload Monthly Sales File (CSV or Excel)", type=["csv", "xlsx"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully!")

        # --- 2. DATA CLEANING & PREPARATION ---
        df.columns = df.columns.str.strip()

        # Determine Total Sale column (handling variations like 'Total Sale' or 'Item Total')
        if "Total Sale" in df.columns:
            revenue_col = "Total Sale"
        elif "Item Total" in df.columns:
            revenue_col = "Item Total"
        else:
            df["Calculated_Total"] = df["Item Rate"] * df["Item Qty."]
            revenue_col = "Calculated_Total"

        total_revenue = df[revenue_col].sum()

        # --- 3. DASHBOARD TABS ---
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📈 Executive Summary",
                "🏥 Departments & Doctors",
                "👤 MPO Performance",
                "🎯 Dynamic MPO Target Setter",
            ]
        )

        with tab1:
            st.subheader("Executive Performance Summary")
            total_invoices = (
                df["Invoice No"].nunique() if "Invoice No" in df.columns else len(df)
            )
            total_cancellations = (
                df["Cencel Qty"].sum() if "Cencel Qty" in df.columns else 0
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Net Revenue", f"৳{total_revenue:,.2f}")
            col2.metric("Total Invoices", f"{total_invoices:,}")
            col3.metric("Total Cancelled Qty", f"{total_cancellations:,}")

            if "Department" in df.columns:
                dept_sales = df.groupby("Department")[
                    revenue_col].sum().reset_index()
                fig_dept = px.bar(
                    dept_sales,
                    x="Department",
                    y=revenue_col,
                    title="Revenue by Department (in BDT)",
                    color="Department",
                )
                st.plotly_chart(fig_dept, use_container_width=True)

        with tab2:
            st.subheader("Top Referral Doctors Analysis")
            if "Referral Doctor" in df.columns:
                doc_sales = (
                    df.groupby("Referral Doctor")[revenue_col]
                    .sum()
                    .reset_index()
                    .sort_values(by=revenue_col, ascending=False)
                    .head(10)
                )
                fig_doc = px.bar(
                    doc_sales,
                    x="Referral Doctor",
                    y=revenue_col,
                    title="Top 10 Referral Doctors by Revenue (in BDT)",
                    color=revenue_col,
                )
                st.plotly_chart(fig_doc, use_container_width=True)
                st.dataframe(doc_sales, use_container_width=True)

        with tab3:
            st.subheader("MPO Productivity Breakdown")
            if "MPO Name" in df.columns:
                mpo_summary = (
                    df.groupby("MPO Name")[revenue_col]
                    .sum()
                    .reset_index()
                    .sort_values(by=revenue_col, ascending=False)
                )
                mpo_summary["Market Share (%)"] = (
                    mpo_summary[revenue_col] / total_revenue
                ) * 100

                fig_mpo = px.bar(
                    mpo_summary,
                    x="MPO Name",
                    y=revenue_col,
                    title="Revenue & Share per MPO (in BDT)",
                    color="MPO Name",
                )
                st.plotly_chart(fig_mpo, use_container_width=True)
                st.dataframe(mpo_summary, use_container_width=True)

        with tab4:
            st.markdown("### 🎯 Dynamic MPO Target Allocation Matrix")
            st.markdown(
                "Set an overarching company growth target, then fine-tune individual"
                " MPO growth factors dynamically."
            )

            if "MPO Name" in df.columns:
                mpo_df = (
                    df.groupby("MPO Name")[revenue_col]
                    .sum()
                    .reset_index()
                    .rename(columns={revenue_col: "Current_Sales"})
                )

                global_growth = st.slider(
                    "Overall Target Company Growth Rate (%)",
                    min_value=0,
                    max_value=50,
                    value=15,
                )
                target_company_revenue = total_revenue * \
                    (1 + global_growth / 100)

                st.info(
                    f"Current Month Total: **৳{total_revenue:,.2f}** | Next Month"
                    f" Company Goal ({global_growth}%):"
                    f" **৳{target_company_revenue:,.2f}**"
                )

                st.markdown(
                    "#### Adjust Individual Growth Multipliers per MPO")

                mpo_targets = []
                for index, row in mpo_df.iterrows():
                    mpo_name = row["MPO Name"]
                    current_val = row["Current_Sales"]

                    col_a, col_b = st.columns([2, 3])
                    with col_a:
                        st.text(f"MPO: {mpo_name} (৳{current_val:,.2f})")
                    with col_b:
                        ind_growth = st.slider(
                            f"Growth % for {mpo_name}",
                            min_value=-10,
                            max_value=60,
                            value=global_growth,
                            key=f"mpo_slider_{mpo_name}",
                        )

                    assigned_target = current_val * (1 + ind_growth / 100)
                    mpo_targets.append({
                        "MPO Name": mpo_name,
                        "Current Sales": current_val,
                        "Growth Rate (%)": ind_growth,
                        "Target Sale": assigned_target,
                    })

                target_df = pd.DataFrame(mpo_targets)
                sum_assigned_targets = target_df["Target Sale"].sum()

                st.markdown("---")
                st.subheader("📋 Final MPO Target Distribution Summary")
                st.dataframe(target_df, use_container_width=True)

                col_t1, col_t2 = st.columns(2)
                col_t1.metric(
                    "Sum of MPO Individual Targets", f"৳{sum_assigned_targets:,.2f}"
                )
                col_t2.metric(
                    "Target vs Company Goal Gap",
                    f"৳{sum_assigned_targets - target_company_revenue:,.2f}",
                )

                target_csv = target_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download MPO Target Report (CSV)",
                    data=target_csv,
                    file_name="next_month_mpo_targets.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Column 'MPO Name' not found in your dataset.")

        # --- 5. FULL CLEAN DATA EXPORT ---
        st.markdown("---")
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Processed Clean Data (CSV)",
            data=csv_data,
            file_name="processed_sales_report.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👆 Please upload your monthly sales Excel or CSV file to begin.")
