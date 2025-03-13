import streamlit as st
import pandas as pd
import gspread
import matplotlib.pyplot as plt
import seaborn as sns
from openpyxl import load_workbook
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import uuid

# -------------------- CONFIGURATION --------------------
EXCEL_FILE = "church_financial_records.xlsx"
GOOGLE_SHEET_NAME = "Church Financial Records"
USE_GOOGLE_SHEETS = False  # Change to True to use Google Sheets
CREDENTIALS_FILE = "credentials.json"  # Google API Credentials

# -------------------- LOAD DATA --------------------
def load_data():
    if USE_GOOGLE_SHEETS:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    else:
        try:
            return pd.read_excel(EXCEL_FILE, sheet_name="Records")
        except FileNotFoundError:
            return pd.DataFrame(columns=["Transaction ID", "Date", "Category", "Subhead", "Debit", "Credit", "Balance", "User"])

# -------------------- SAVE DATA --------------------
def save_data(df):
    if USE_GOOGLE_SHEETS:
        client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope))
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
    else:
        with pd.ExcelWriter(EXCEL_FILE, mode="w", engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Records", index=False)

# -------------------- ADD OR EDIT TRANSACTION --------------------
def add_or_edit_transaction(transaction_id, date, category, subhead, debit, credit, user):
    df = load_data()
    if transaction_id in df["Transaction ID"].values:
        df.loc[df["Transaction ID"] == transaction_id, ["Date", "Category", "Subhead", "Debit", "Credit", "User"]] = [date, category, subhead, debit, credit, user]
    else:
        new_entry = {"Transaction ID": generate_transaction_id(), "Date": date, "Category": category, "Subhead": subhead, "Debit": debit, "Credit": credit, "User": user}
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df["Balance"] = df["Credit"].sum() - df["Debit"].sum()
    save_data(df)

# -------------------- GENERATE TRANSACTION ID --------------------
def generate_transaction_id():
    df = load_data()
    last_id = df["Transaction ID"].dropna().tolist()
    if not last_id:
        return "A0001"
    last_id = sorted(last_id)[-1]
    letter, num = last_id[0], int(last_id[1:])
    if num < 9999:
        return f"{letter}{num+1:04d}"
    else:
        return f"{chr(ord(letter)+1)}0001"

# -------------------- DELETE TRANSACTION --------------------
def delete_transaction(transaction_id):
    df = load_data()
    df = df[df["Transaction ID"] != transaction_id]
    save_data(df)

# -------------------- UNDO LAST ACTION --------------------
def undo_last_action():
    df = load_data()
    df = df.iloc[:-1]
    save_data(df)

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="Church Financial Records", layout="wide")
st.title("\U0001F4B8 Church Financial Record Management")

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["Dashboard", "Add/Edit Transaction", "Delete Transaction", "Undo Last Action"])

# Load data
df = load_data()

if menu == "Dashboard":
    st.subheader("Financial Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"₦{df['Credit'].sum():,.2f}")
    col2.metric("Total Expenditure", f"₦{df['Debit'].sum():,.2f}")
    col3.metric("Balance", f"₦{df['Balance'].iloc[-1]:,.2f}")
    st.write("### Recent Transactions")
    st.dataframe(df.sort_values(by="Date", ascending=False).head(10))

elif menu == "Add/Edit Transaction":
    st.subheader("Add or Edit Transaction")
    transaction_id = st.text_input("Transaction ID (Leave blank for new)")
    date = st.date_input("Date")
    category = st.selectbox("Category", ["Weekly Collection", "Freewill Donation", "Fundraising", "Expenditure"])
    subhead = st.text_input("Subhead")
    debit = st.number_input("Debit (Amount Spent)", min_value=0.0, format="%.2f")
    credit = st.number_input("Credit (Amount Received)", min_value=0.0, format="%.2f")
    user = st.selectbox("User", ["Guest", "Treasurer"])
    
    if st.button("Save Transaction"):
        add_or_edit_transaction(transaction_id, date, category, subhead, debit, credit, user)
        st.success("Transaction saved successfully!")

elif menu == "Delete Transaction":
    st.subheader("Delete Transaction")
    transaction_id = st.selectbox("Select Transaction to Delete", df["Transaction ID"].tolist())
    if st.button("Delete"):
        delete_transaction(transaction_id)
        st.success("Transaction deleted successfully!")

elif menu == "Undo Last Action":
    st.subheader("Undo Last Action")
    if st.button("Undo"):
        undo_last_action()
        st.success("Last action undone!")
