import streamlit as st
import pandas as pd
import string
from openpyxl import load_workbook

# -------------------- CONFIGURATION --------------------
EXCEL_FILE = "church_financial_records.xlsx"

# -------------------- LOAD DATA --------------------
def load_data():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="Records", dtype={"Transaction ID": str})
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Transaction ID", "Date", "Category", "Subhead", "Debit", "Credit", "Balance"])
    
    # Convert types
    df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce").fillna(0.0).astype(float)
    df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce").fillna(0.0).astype(float)
    df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce").fillna(0.0).astype(float)

    return df

# -------------------- SAVE DATA --------------------
def save_data(df):
    with pd.ExcelWriter(EXCEL_FILE, mode="w", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Records", index=False)

# -------------------- TRANSACTION ID GENERATION --------------------
def generate_transaction_id(df):
    if df.empty:
        return "a0001"

    last_id = df["Transaction ID"].dropna().iloc[-1]
    letter, num = last_id[0], int(last_id[1:])
    
    if num < 9999:
        return f"{letter}{num+1:04d}"
    else:
        next_letter = string.ascii_lowercase[string.ascii_lowercase.index(letter) + 1]
        return f"{next_letter}0001"

# -------------------- ADD OR EDIT TRANSACTION --------------------
def add_or_edit_transaction(transaction_id, date, category, subhead, debit, credit):
    df = load_data()

    # Ensure numerical values
    debit = float(debit) if debit else 0.0
    credit = float(credit) if credit else 0.0

    if transaction_id and transaction_id in df["Transaction ID"].values:
        # Edit existing transaction
        df.loc[df["Transaction ID"] == transaction_id, ["Date", "Category", "Subhead", "Debit", "Credit"]] = [date, category, subhead, debit, credit]
    else:
        # Add new transaction
        new_entry = {
            "Transaction ID": generate_transaction_id(df),
            "Date": date,
            "Category": category,
            "Subhead": subhead,
            "Debit": debit,
            "Credit": credit,
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)

    # Recalculate balance
    df["Balance"] = df["Credit"].sum() - df["Debit"].sum()
    save_data(df)

# -------------------- STREAMLIT UI --------------------
st.title("Church Financial Record Management System")

menu = st.sidebar.selectbox("Select an option", ["Add or Edit Transaction", "View Reports"])

if menu == "Add or Edit Transaction":
    st.subheader("Add or Edit Transaction")

    df = load_data()

    # Ensure there are transactions before allowing selection
    transaction_ids = df["Transaction ID"].dropna().tolist() if not df.empty else []
    transaction_id = st.selectbox("Select transaction to edit (or leave blank to add new)", [""] + transaction_ids)

    # Initialize form fields
    date, category, subhead, debit, credit = None, "", "", 0.0, 0.0

    if transaction_id:
        # Retrieve existing data only if a valid transaction is selected
        transaction_data = df[df["Transaction ID"] == transaction_id]
        if not transaction_data.empty:
            transaction_data = transaction_data.iloc[0]
            date = pd.to_datetime(transaction_data["Date"]).date()
            category = transaction_data["Category"]
            subhead = transaction_data["Subhead"]
            debit = float(transaction_data["Debit"])
            credit = float(transaction_data["Credit"])

    # Input Fields
    date = st.date_input("Date", value=date)
    category = st.selectbox("Category", ["Weekly Collection", "Freewill Donation", "Fundraising", "Expenditure"], 
                            index=["Weekly Collection", "Freewill Donation", "Fundraising", "Expenditure"].index(category) if category else 0)
    subhead = st.text_input("Subhead (Enter new or select existing)", value=subhead)
    debit = st.number_input("Debit (Amount Spent)", min_value=0.0, format="%.2f", value=debit)
    credit = st.number_input("Credit (Amount Received)", min_value=0.0, format="%.2f", value=credit)

    if st.button("Save Transaction"):
        add_or_edit_transaction(transaction_id, date, category, subhead, debit, credit)
        st.success("Transaction Saved Successfully!")

elif menu == "View Reports":
    st.subheader("Financial Reports")

    df = load_data()
    st.dataframe(df)
