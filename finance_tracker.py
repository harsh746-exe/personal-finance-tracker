import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Set page config
st.set_page_config(page_title="Personal Finance Tracker", layout="wide")

# Initialize session state for expenses and income if they don't exist
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=['Date', 'Category', 'Description', 'Amount', 'Type'])
if 'income' not in st.session_state:
    st.session_state.income = pd.DataFrame(columns=['Date', 'Source', 'Description', 'Amount'])
if 'budgets' not in st.session_state:
    st.session_state.budgets = {
        "Food & Dining": 500,
        "Transportation": 300,
        "Housing": 2000,
        "Entertainment": 200,
        "Shopping": 300,
        "Utilities": 400,
        "Healthcare": 300,
        "Other": 200
    }

# Title and description
st.title("💰 Personal Finance Tracker")
st.markdown("Track your income, expenses, and analyze your financial patterns")

# Sidebar for adding transactions
with st.sidebar:
    st.header("Add New Transaction")
    
    # Transaction type selection
    transaction_type = st.radio("Transaction Type", ["Expense", "Income"])
    
    # Date input
    date = st.date_input("Date", datetime.now())
    
    if transaction_type == "Expense":
        # Category selection for expenses
        category = st.selectbox(
            "Category",
            ["Food & Dining", "Transportation", "Housing", "Entertainment", 
             "Shopping", "Utilities", "Healthcare", "Other"]
        )
        # Description input
        description = st.text_input("Description", "")
        # Amount input
        amount = st.number_input("Amount ($)", min_value=0.0, step=10.0)
        
        # Add expense button
        if st.button("Add Expense"):
            if description and amount > 0:
                new_expense = pd.DataFrame({
                    'Date': [pd.to_datetime(date)],
                    'Category': [category],
                    'Description': [description],
                    'Amount': [amount],
                    'Type': ['Expense']
                })
                st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
                st.success("Expense added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields correctly!")
    
    else:  # Income
        # Income source selection
        source = st.selectbox(
            "Income Source",
            ["Salary", "Freelance", "Investments", "Other"]
        )
        # Description input
        description = st.text_input("Description", "")
        # Amount input
        amount = st.number_input("Amount ($)", min_value=0.0, step=100.0)
        
        # Add income button
        if st.button("Add Income"):
            if description and amount > 0:
                new_income = pd.DataFrame({
                    'Date': [pd.to_datetime(date)],
                    'Source': [source],
                    'Description': [description],
                    'Amount': [amount]
                })
                st.session_state.income = pd.concat([st.session_state.income, new_income], ignore_index=True)
                st.success("Income added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields correctly!")

# Main content area
col1, col2 = st.columns(2)

with col1:
    # Summary statistics
    st.subheader("📊 Financial Summary")
    if not st.session_state.expenses.empty or not st.session_state.income.empty:
        total_expenses = st.session_state.expenses['Amount'].sum() if not st.session_state.expenses.empty else 0
        total_income = st.session_state.income['Amount'].sum() if not st.session_state.income.empty else 0
        net_income = total_income - total_expenses
        
        st.metric("Total Income", f"${total_income:,.2f}")
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
        st.metric("Net Income", f"${net_income:,.2f}", 
                 delta=f"{'${:,.2f}'.format(net_income)}" if net_income != 0 else None)
    else:
        st.info("No transactions recorded yet. Add some transactions using the sidebar!")

with col2:
    # Category breakdown
    st.subheader("📈 Expense Breakdown")
    if not st.session_state.expenses.empty:
        category_totals = st.session_state.expenses.groupby('Category')['Amount'].sum()
        fig = px.pie(values=category_totals.values, 
                    names=category_totals.index,
                    title="Expenses by Category")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses to display yet!")

# Budget tracking
st.subheader("💰 Budget Tracking")
if not st.session_state.expenses.empty:
    budget_df = pd.DataFrame({
        'Category': list(st.session_state.budgets.keys()),
        'Budget': list(st.session_state.budgets.values())
    })
    
    # Calculate actual spending
    actual_spending = st.session_state.expenses.groupby('Category')['Amount'].sum().reset_index()
    budget_df = budget_df.merge(actual_spending, on='Category', how='left')
    budget_df['Amount'] = budget_df['Amount'].fillna(0)
    budget_df['Remaining'] = budget_df['Budget'] - budget_df['Amount']
    budget_df['Progress'] = (budget_df['Amount'] / budget_df['Budget'] * 100).round(1)
    
    # Display budget progress bars
    for _, row in budget_df.iterrows():
        st.write(f"**{row['Category']}**")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.progress(min(row['Progress'] / 100, 1.0))
        with col2:
            st.write(f"${row['Amount']:,.0f} / ${row['Budget']:,.0f}")
        with col3:
            st.write(f"{row['Progress']}%")
else:
    st.info("No expenses to track against budget yet!")

# Recent transactions
st.subheader("📝 Recent Transactions")
if not st.session_state.expenses.empty or not st.session_state.income.empty:
    # Combine expenses and income for display
    recent_expenses = st.session_state.expenses.copy()
    recent_expenses['Date'] = recent_expenses['Date'].dt.strftime('%Y-%m-%d')
    
    recent_income = st.session_state.income.copy()
    recent_income['Date'] = recent_income['Date'].dt.strftime('%Y-%m-%d')
    
    # Display expenses
    if not recent_expenses.empty:
        st.write("**Expenses**")
        st.dataframe(
            recent_expenses[['Date', 'Category', 'Description', 'Amount']]
            .sort_values('Date', ascending=False),
            use_container_width=True
        )
    
    # Display income
    if not recent_income.empty:
        st.write("**Income**")
        st.dataframe(
            recent_income[['Date', 'Source', 'Description', 'Amount']]
            .sort_values('Date', ascending=False),
            use_container_width=True
        )
else:
    st.info("No transactions recorded yet!")

# Monthly trend
st.subheader("📅 Monthly Financial Trend")
if not st.session_state.expenses.empty or not st.session_state.income.empty:
    # Process expenses
    monthly_expenses = st.session_state.expenses.copy()
    monthly_expenses['Date'] = pd.to_datetime(monthly_expenses['Date'])
    monthly_expenses = monthly_expenses.groupby(
        monthly_expenses['Date'].dt.to_period('M')
    )['Amount'].sum().reset_index()
    
    # Process income
    monthly_income = st.session_state.income.copy()
    monthly_income['Date'] = pd.to_datetime(monthly_income['Date'])
    monthly_income = monthly_income.groupby(
        monthly_income['Date'].dt.to_period('M')
    )['Amount'].sum().reset_index()
    
    # Combine and plot
    monthly_data = pd.merge(
        monthly_expenses, 
        monthly_income, 
        on='Date', 
        how='outer', 
        suffixes=('_expenses', '_income')
    ).fillna(0)
    
    monthly_data['Date'] = monthly_data['Date'].astype(str)
    
    fig = px.line(monthly_data, 
                  x='Date', 
                  y=['Amount_expenses', 'Amount_income'],
                  title="Monthly Income vs Expenses",
                  labels={'value': 'Amount ($)', 'variable': 'Type'})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for trend analysis!")

# Add some helpful tips
with st.expander("💡 Tips for Better Financial Management"):
    st.markdown("""
    1. **Track Every Transaction**: Record all your income and expenses, no matter how small
    2. **Categorize Wisely**: Use specific categories to better understand your spending
    3. **Review Regularly**: Check your spending patterns weekly or monthly
    4. **Set and Monitor Budgets**: Create category-specific budgets and track your progress
    5. **Identify Trends**: Look for patterns in your income and spending to make better decisions
    6. **Emergency Fund**: Try to maintain 3-6 months of expenses in savings
    7. **Regular Income**: Consider setting up automatic transfers for savings
    8. **Review Subscriptions**: Regularly check and cancel unused subscriptions
    """) 