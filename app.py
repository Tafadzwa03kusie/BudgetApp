import json

import pandas as pd
import plotly.express as px
import streamlit as st

# Set the page configuration before any other Streamlit commands
st.set_page_config(page_title="Expense Tracker", layout="wide")

# Set global display format for pandas
pd.options.display.float_format = "{:.2f}".format

# JSON file for storing predefined budgets
BUDGET_FILE = 'budget_mapper.json'

data = pd.read_csv('Expenses tr.csv', skiprows=13, sep=";", parse_dates=['Date'])

# Load or initialize the budget mapper JSON and ensure all budget amounts are rounded to two decimal places
try:
    with open(BUDGET_FILE, 'r') as f:
        budget_mapper = json.load(f)
    # Ensure all budget amounts have two decimal places
    for desc, details in budget_mapper.items():
        details["Budget Amount"] = round(float(details["Budget Amount"]), 2)
except FileNotFoundError:
    budget_mapper = {}
    with open(BUDGET_FILE, 'w') as f:
        json.dump(budget_mapper, f)

# Populate the budget mapper with CSV data if empty
if not budget_mapper:
    for _, row in data.iterrows():
        description = row['Description']
        category = row['Category']
        budget_amount = round(row['Budget Amount'], 2)  # Ensure two decimal places

        if description not in budget_mapper:
            budget_mapper[description] = {
                "Category": category,
                "Budget Amount": budget_amount
            }

    # Save to JSON file with properly formatted amounts
    with open(BUDGET_FILE, 'w') as f:
        json.dump(budget_mapper, f)

# Title and Sidebar
st.title("Personal Finance Dashboard - Created by Tafadzwa Melissa Kusikwenyu")
st.sidebar.title("Menu")
menu = st.sidebar.radio("Select an Option", ["Budget Management", "Budget Planning", "Reporting", "Data Visualization"])

# Budget Management Dashboard
if menu == "Budget Management":
    st.header("Manage Predefined Budgets")

    # Text input fields for Category and Description
    with st.form("add_budget"):
        description = st.text_input("Enter Description")
        category = st.text_input("Enter Category")
        budget_amount = st.number_input("Budget Amount", min_value=0.0, format="%.2f")
        add_budget = st.form_submit_button("Add/Update Budget")

    if add_budget:
        if description and category:  # Only save if both fields are filled
            budget_mapper[description] = {"Category": category, "Budget Amount": round(budget_amount, 2)}
            with open(BUDGET_FILE, 'w') as f:
                json.dump(budget_mapper, f)
            st.success("Budget entry added/updated successfully!")
        else:
            st.error("Please enter both a category and description.")

    # Convert budget_mapper to a DataFrame for display and apply formatting
    budget_df = pd.DataFrame([
        {"Description": desc, "Category": details["Category"],
         "Budget Amount": "{:.2f}".format(details["Budget Amount"])}
        for desc, details in budget_mapper.items()
    ])

    # Display the budget mapper as a table
    st.write("Current Budget Mapper:")
    st.table(budget_df)

# Budget Planning
elif menu == "Budget Planning":
    st.header("Budget Planning")
    st.write("Input your planned expenses by category and date. Predefined budgets are loaded automatically.")

    # Allow new category entry if it doesn't exist
    with st.form("budget_form"):
        date = st.date_input("Date")
        description = st.selectbox("Description", options=budget_mapper.keys())
        predefined_budget = budget_mapper[description]["Budget Amount"]
        category = st.text_input("Category", value=budget_mapper[description]["Category"])
        st.write(f"Budget Amount (auto-filled): ${predefined_budget}")
        actual_amount = st.number_input("Actual Amount", min_value=0.0)
        submitted = st.form_submit_button("Add Budget Entry")

    # When the form is submitted, add the entry
    if submitted:
        # Update the budget mapper with the new category if it doesn't exist
        if description not in budget_mapper:
            budget_mapper[description] = {"Category": category, "Budget Amount": predefined_budget}
            with open(BUDGET_FILE, 'w') as f:
                json.dump(budget_mapper, f)

        # Add the entry to the data table
        new_entry = pd.DataFrame({
            'Date': [pd.to_datetime(date)],  # Ensure date is in datetime format
            'Category': [category],
            'Description': [description],
            'Budget Amount': [predefined_budget],
            'Actual Amount': [actual_amount],
            'Difference': [predefined_budget - actual_amount]
        })
        data = pd.concat([data, new_entry], ignore_index=True)

        # Ensure the entire Date column is in datetime format to avoid conversion issues
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

        st.success("Budget entry added successfully!")

    # Display all budget entries
    st.write("All Budget Entries")
    st.dataframe(data)

# Reporting
elif menu == "Reporting":
    st.header("Financial Reporting")

    # Date filter for reporting
    st.subheader("Select Date Range")
    start_date = st.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
    end_date = st.date_input("End Date", value=pd.to_datetime("2024-12-31"))

    # Filter data based on selected date range
    filtered_data = data[(data["Date"] >= pd.to_datetime(start_date)) & (data["Date"] <= pd.to_datetime(end_date))]

    # Calculate summaries
    st.subheader("Summary Report")
    total_budget = filtered_data["Budget Amount"].sum()
    total_actual = filtered_data["Actual Amount"].sum()
    total_difference = filtered_data["Difference"].sum()

    st.write(f"Total Budget Amount: ${total_budget}")
    st.write(f"Total Actual Amount: ${total_actual}")
    st.write(f"Total Difference: ${total_difference}")

    # Display filtered data
    st.write("Detailed Records:")
    st.dataframe(filtered_data)

# Data Visualization
elif menu == "Data Visualization":
    st.header("Data Visualization")

    # Filter data based on date range for visualization
    start_date = st.date_input("Start Date", value=pd.to_datetime("2024-01-01"), key="viz_start")
    end_date = st.date_input("End Date", value=pd.to_datetime("2024-12-31"), key="viz_end")
    filtered_data = data[(data["Date"] >= pd.to_datetime(start_date)) & (data["Date"] <= pd.to_datetime(end_date))]

    # Expense Category Pie Chart
    st.subheader("Expense Distribution by Category")
    category_expense = filtered_data.groupby("Category")["Actual Amount"].sum().reset_index()
    fig1 = px.pie(category_expense, values='Actual Amount', names='Category',
                  title="Actual Expense Distribution by Category")
    st.plotly_chart(fig1)

    # Budget vs Actual over time
    st.subheader("Budget vs Actual Trend Over Time")
    trend_data = filtered_data.groupby("Date")[["Budget Amount", "Actual Amount"]].sum().reset_index()
    fig2 = px.line(trend_data, x="Date", y=["Budget Amount", "Actual Amount"], title="Budget vs Actual Over Time")
    st.plotly_chart(fig2)

# Footer
st.sidebar.write("---")
st.sidebar.write("Personal Finance Dashboard - Created by Tafadzwa Melissa Kusikwenyu")
