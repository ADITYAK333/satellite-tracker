# filename: smart_excel_analyzer.py

import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import re

# Page setup
st.set_page_config(page_title="Smart Excel Analyzer", layout="wide")
st.title("📊 Smart Excel Data Analyzer")

# Upload section
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
if uploaded_file:
    sheet_names = pd.ExcelFile(uploaded_file).sheet_names
    selected_sheet = st.selectbox("Choose sheet", sheet_names)
    df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

    st.subheader("🧹 Raw Data Preview")
    st.dataframe(df.head())

    # Clean function
    def clean_data(df):
        df = df.copy()
        # Price cleanup
        if 'Price' in df.columns:
            df['Price (INR)'] = df['Price'].replace('[₹,]', '', regex=True).astype(str).str.extract('(\d+)').astype(float)

        # Rating Value cleanup
        if 'Rating Value' in df.columns:
            df['Rating'] = df['Rating Value'].str.extract(r'([\d\.]+)').astype(float)

        # Rating Count cleanup
        if 'Rating Count' in df.columns:
            df['Rating Count'] = df['Rating Count'].replace(',', '', regex=True).astype(str).str.extract('(\d+)').astype(float)

        # Original Price
        if 'Original Price' in df.columns:
            df['Original Price (INR)'] = df['Original Price'].replace('[₹,]', '', regex=True).astype(str).str.extract('(\d+)').astype(float)

        # Discount Extraction
        if 'Discount Percentage' in df.columns:
            df['Discount (%)'] = df['Discount Percentage'].str.extract(r'(\d+)%').astype(float)

        return df

    df = clean_data(df)

    st.subheader("📌 Cleaned Data Overview")
    st.dataframe(df.head())

    # User Analysis Intent
    st.markdown("### 🤖 What would you like to analyze?")
    query = st.text_input("Type your question (e.g. Show rating vs price trend)", "")

    # Process some example intents
    if query:
        if "price vs rating" in query.lower():
            fig, ax = plt.subplots()
            sns.scatterplot(data=df, x="Price (INR)", y="Rating", size="Rating Count", hue="Discount (%)", ax=ax)
            st.pyplot(fig)

        elif "top rated" in query.lower():
            top_n = df.sort_values(by="Rating", ascending=False).head(10)
            st.write("🔝 Top Rated Products")
            st.dataframe(top_n[["Product Name", "Rating", "Price (INR)", "Rating Count"]])

        elif "discount" in query.lower():
            fig, ax = plt.subplots()
            sns.histplot(df["Discount (%)"].dropna(), bins=20, kde=True)
            st.pyplot(fig)

        elif "summary" in query.lower():
            st.write(df.describe(include='all'))

        else:
            st.warning("⚠️ Query not recognized. Try asking for 'top rated', 'price vs rating', or 'discount distribution'.")

    # Allow custom visual exploration
    st.markdown("### 📈 Custom Plot")
    x_col = st.selectbox("X-axis", df.columns)
    y_col = st.selectbox("Y-axis", df.columns)
    if st.button("Generate Plot"):
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x=x_col, y=y_col, ax=ax)
        st.pyplot(fig)
