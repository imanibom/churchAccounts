import streamlit as st
import pandas as pd
import plotly.express as px

# Load or initialize transaction data
def load_data():
    try:
        df = pd.read_csv("transactions.csv")
        df["Date"] = pd.to_datetime(df["Date"]).dt.date  # Convert Date column to date format
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Category", "Subhead", "Amount", "User"])

data = load_data()

st.title("Church Financial Record Management System")

# Define available categories
categories = ["Sunday Collections", "Donations", "Fundraising", "Expenditure"]
users = ["Guest", "Treasurer", "Financial Secretary"]

# Set up tab layout
tab1, tab2, tab3 = st.tabs(["➕ Add Transactions", "📝 Edit Transactions", "📊 Summary and Report"])

with tab1:
    st.subheader("Add Transactions")

    # Date dropdown (Existing dates in data or new selection)
    unique_dates = sorted(data["Date"].unique()) if not data.empty else []
    date = st.selectbox("Select Date", unique_dates + ["New Date"], index=0)

    if date == "New Date":
        date = st.date_input("Pick a New Date")

    # Table for transaction entry
    new_data = pd.DataFrame(
        {
            "Date": [date] * 3,  # Pre-fill with selected date
            "Category": [""] * 3,
            "Subhead": [""] * 3,
            "Amount": [0.0] * 3,
            "User": ["Guest"] * 3,
        }
    )

    edited_data = st.data_editor(
        new_data,
        num_rows="dynamic",
        column_config={
            "Category": st.column_config.SelectboxColumn("Category", options=categories),
            "User": st.column_config.SelectboxColumn("User", options=users),
        },
    )

    if st.button("Save Transactions"):
        edited_data["Date"] = date  # Ensure the selected date is applied
        data = pd.concat([data, edited_data], ignore_index=True)
        data.to_csv("transactions.csv", index=False)
        st.success("Transactions Saved!")
        st.experimental_rerun()  # Refresh the page

with tab2:
    st.subheader("Edit Transactions")

    if not data.empty:
        transaction_id = st.selectbox("Select Transaction ID", data.index.tolist())
        selected_row = data.iloc[[transaction_id]]  # Select as DataFrame for editing

        edited_row = st.data_editor(
            selected_row,
            column_config={
                "Category": st.column_config.SelectboxColumn("Category", options=categories),
                "User": st.column_config.SelectboxColumn("User", options=users),
            },
        )

        if st.button("Update Transaction"):
            data.iloc[transaction_id] = edited_row.iloc[0]  # Update row
            data.to_csv("transactions.csv", index=False)
            st.success("Transaction Updated!")
            st.experimental_rerun()
    else:
        st.warning("No transactions available to edit.")

with tab3:
    st.subheader("📊 Financial Summary and Report")

    if not data.empty:
        # Summary Table
        total_income = data[~data["Category"].str.contains("Expenditure", na=False)]["Amount"].sum()
        total_expense = data[data["Category"] == "Expenditure"]["Amount"].sum()

        st.metric("💰 Total Income", f"₦{total_income:,.2f}")
        st.metric("💸 Total Expenditure", f"₦{total_expense:,.2f}")
        st.metric("📈 Net Balance", f"₦{total_income - total_expense:,.2f}")

        # Pie Chart - Income vs. Expenditure
        pie_df = pd.DataFrame({
            "Type": ["Income", "Expenditure"],
            "Amount": [total_income, total_expense]
        })
        fig_pie = px.pie(pie_df, names="Type", values="Amount", title="Income vs. Expenditure")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Bar Chart - Category-wise Distribution
        category_summary = data.groupby("Category")["Amount"].sum().reset_index()
        fig_bar = px.bar(category_summary, x="Category", y="Amount", title="Category-wise Transaction Distribution")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Show Data Table
        st.subheader("📜 Recent Transactions")
        st.dataframe(data.tail(10))  # Show last 10 transactions
    else:
        st.warning("No transactions available for summary.")
