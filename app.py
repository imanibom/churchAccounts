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
            return pd.DataFrame(columns=["Date", "Category", "Subhead", "Debit", "Credit", "Balance"])

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

# -------------------- ADD TRANSACTION --------------------
def add_transaction(date, category, subhead, debit, credit):
    df = load_data()
    new_entry = {"Date": date, "Category": category, "Subhead": subhead, "Debit": debit, "Credit": credit}
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df["Balance"] = df["Credit"].sum() - df["Debit"].sum()
    save_data(df)

# -------------------- GENERATE REPORT --------------------
def generate_report(start_date, end_date, category=None, subhead=None):
    df = load_data()
    
    # Convert to datetime for proper comparison
    df["Date"] = pd.to_datetime(df["Date"])
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    if category:
        filtered_df = filtered_df[filtered_df["Category"] == category]
    if subhead:
        filtered_df = filtered_df[filtered_df["Subhead"] == subhead]

    return filtered_df.groupby(["Category", "Subhead"])[["Debit", "Credit"]].sum().reset_index()

# -------------------- EXPORT TO CSV --------------------
def export_to_csv(df):
    csv_data = df.to_csv(index=False).encode("utf-8")
    return csv_data

# -------------------- EXPORT TO PDF --------------------
def export_to_pdf(df):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)

    p.drawString(30, 750, "Financial Report")
    p.drawString(30, 735, "===================")

    y = 700
    for i, row in df.iterrows():
        text = f"{row['Category']} - {row['Subhead']}: Debit={row['Debit']}, Credit={row['Credit']}"
        p.drawString(30, y, text)
        y -= 20
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = 750

    p.save()
    buffer.seek(0)
    return buffer

# -------------------- CREATE CHARTS --------------------
def generate_charts(df):
    st.subheader("Financial Charts")

    # Bar Chart: Income vs. Expenditure
    st.write("### Income vs. Expenditure")
    fig, ax = plt.subplots(figsize=(8, 5))
    df.groupby("Category")[["Debit", "Credit"]].sum().plot(kind="bar", ax=ax)
    st.pyplot(fig)

    # Pie Chart: Expenditure Breakdown
    st.write("### Expenditure Breakdown")
    if not df.empty and "Debit" in df.columns and df["Debit"].sum() > 0:
        fig, ax = plt.subplots(figsize=(6, 6))
        df.groupby("Category")["Debit"].sum().plot(kind="pie", autopct="%1.1f%%", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("No expenditure data available for this period.")

    # Histogram with Trend Line
    st.write("### Financial Trend Over Time")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df["Credit"] - df["Debit"], bins=20, kde=True, ax=ax)
    st.pyplot(fig)

# -------------------- STREAMLIT UI --------------------
st.title("Church Financial Record Management System")

# Sidebar Navigation
menu = st.sidebar.selectbox("Select an option", ["Add Transaction", "View Reports"])

if menu == "Add Transaction":
    st.subheader("Add New Transaction")

    date = st.date_input("Date")
    category = st.selectbox("Category", ["Weekly Collection", "Freewill Donation", "Fundraising", "Expenditure"])
    subhead = st.text_input("Subhead (Enter new or select existing)")
    debit = st.number_input("Debit (Amount Spent)", min_value=0.0, format="%.2f")
    credit = st.number_input("Credit (Amount Received)", min_value=0.0, format="%.2f")

    if st.button("Add Transaction"):
        add_transaction(date, category, subhead, debit, credit)
        st.success("Transaction Added Successfully!")

elif menu == "View Reports":
    st.subheader("Generate Financial Reports")

    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    category_filter = st.selectbox("Category (Optional)", ["All"] + ["Weekly Collection", "Freewill Donation", "Fundraising", "Expenditure"])
    subhead_filter = st.text_input("Subhead (Optional)")

    if st.button("Generate Report"):
        report_df = generate_report(start_date, end_date, category_filter if category_filter != "All" else None, subhead_filter)
        st.dataframe(report_df)
        generate_charts(report_df)

        # Download CSV
        csv_data = export_to_csv(report_df)
        st.download_button(label="Download as CSV", data=csv_data, file_name="financial_report.csv", mime="text/csv")

        # Download PDF
        pdf_data = export_to_pdf(report_df)
        st.download_button(label="Download as PDF", data=pdf_data, file_name="financial_report.pdf", mime="application/pdf")
