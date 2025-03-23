import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import yfinance as yf
import numpy as np
from pathlib import Path

# Constants
CURRENCIES = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'INR': '₹'
}

INVESTMENT_CATEGORIES = [
    'Stocks',
    'Mutual Funds',
    'ETFs',
    'Bonds',
    'Cryptocurrency',
    'Real Estate'
]

DEBT_CATEGORIES = [
    'Credit Card',
    'Personal Loan',
    'Home Loan',
    'Student Loan',
    'Car Loan',
    'Other'
]

GOAL_CATEGORIES = [
    'Emergency Fund',
    'Retirement',
    'Home Down Payment',
    'Vacation',
    'Education',
    'Other'
]

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'income' not in st.session_state:
    st.session_state.income = []
if 'investments' not in st.session_state:
    st.session_state.investments = []
if 'debts' not in st.session_state:
    st.session_state.debts = []
if 'goals' not in st.session_state:
    st.session_state.goals = []
if 'bills' not in st.session_state:
    st.session_state.bills = []
if 'selected_currency' not in st.session_state:
    st.session_state.selected_currency = 'USD'
if 'recurring_transactions' not in st.session_state:
    st.session_state.recurring_transactions = []

# Helper Functions
def format_currency(amount: float) -> str:
    return f"{CURRENCIES[st.session_state.selected_currency]}{amount:,.2f}"

def calculate_investment_returns(investment: Dict) -> float:
    if investment['type'] == 'Stocks':
        try:
            stock = yf.Ticker(investment['symbol'])
            current_price = stock.info.get('regularMarketPrice', 0)
            return (current_price - investment['purchase_price']) * investment['quantity']
        except:
            return 0
    return 0

def calculate_debt_payment_schedule(debt: Dict) -> List[Dict]:
    monthly_rate = debt['interest_rate'] / 12 / 100
    monthly_payment = debt['amount'] * (monthly_rate * (1 + monthly_rate)**debt['term_months']) / ((1 + monthly_rate)**debt['term_months'] - 1)
    schedule = []
    balance = debt['amount']
    
    for month in range(1, debt['term_months'] + 1):
        interest = balance * monthly_rate
        principal = monthly_payment - interest
        balance -= principal
        schedule.append({
            'month': month,
            'payment': monthly_payment,
            'principal': principal,
            'interest': interest,
            'balance': max(0, balance)
        })
    return schedule

def calculate_goal_progress(goal: Dict) -> float:
    return (goal['current_amount'] / goal['target_amount']) * 100

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Transactions", "Investments", "Debts", "Goals", "Bills", "Reports"])

# Main Content
st.title("Personal Finance Dashboard")

if page == "Dashboard":
    # Create tabs for different dashboard views
    tab1, tab2, tab3 = st.tabs(["Overview", "Analytics", "Trends"])
    
    with tab1:
        # Financial Summary Cards
        col1, col2, col3 = st.columns(3)
        
        total_income = sum(income['amount'] for income in st.session_state.income)
        total_expenses = sum(expense['amount'] for expense in st.session_state.transactions)
        net_worth = total_income - total_expenses
        
        col1.metric("Total Income", format_currency(total_income), 
                   delta=format_currency(total_income - (sum(income['amount'] for income in st.session_state.income[:-1]) if len(st.session_state.income) > 1 else 0)))
        col2.metric("Total Expenses", format_currency(total_expenses),
                   delta=format_currency(total_expenses - (sum(expense['amount'] for expense in st.session_state.transactions[:-1]) if len(st.session_state.transactions) > 1 else 0)))
        col3.metric("Net Worth", format_currency(net_worth),
                   delta=format_currency(net_worth - ((sum(income['amount'] for income in st.session_state.income[:-1]) - sum(expense['amount'] for expense in st.session_state.transactions[:-1])) if len(st.session_state.income) > 1 or len(st.session_state.transactions) > 1 else 0)))
        
        # Investment Portfolio Summary
        st.subheader("Investment Portfolio")
        portfolio_value = sum(investment['amount'] for investment in st.session_state.investments)
        portfolio_returns = sum(calculate_investment_returns(investment) for investment in st.session_state.investments)
        
        col1, col2 = st.columns(2)
        col1.metric("Portfolio Value", format_currency(portfolio_value))
        col2.metric("Total Returns", format_currency(portfolio_returns),
                   delta=format_currency(portfolio_returns - (sum(calculate_investment_returns(investment) for investment in st.session_state.investments[:-1]) if len(st.session_state.investments) > 1 else 0)))
        
        # Debt Summary
        st.subheader("Debt Overview")
        total_debt = sum(debt['amount'] for debt in st.session_state.debts)
        monthly_debt_payments = sum(debt.get('monthly_payment', 0) for debt in st.session_state.debts)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Debt", format_currency(total_debt))
        col2.metric("Monthly Payments", format_currency(monthly_debt_payments))
        
        # Financial Goals Progress
        st.subheader("Financial Goals")
        for goal in st.session_state.goals:
            progress = calculate_goal_progress(goal)
            st.progress(progress)
            st.write(f"{goal['name']}: {format_currency(goal['current_amount'])} / {format_currency(goal['target_amount'])}")
    
    with tab2:
        # Interactive Analytics
        st.subheader("Financial Analytics")
        
        # Income vs Expenses Chart
        if st.session_state.income or st.session_state.transactions:
            fig = go.Figure()
            
            # Add income bars
            income_data = pd.DataFrame(st.session_state.income)
            if not income_data.empty:
                fig.add_trace(go.Bar(
                    x=income_data['date'],
                    y=income_data['amount'],
                    name='Income',
                    marker_color='green'
                ))
            
            # Add expense bars
            expense_data = pd.DataFrame(st.session_state.transactions)
            if not expense_data.empty:
                fig.add_trace(go.Bar(
                    x=expense_data['date'],
                    y=expense_data['amount'],
                    name='Expenses',
                    marker_color='red'
                ))
            
            fig.update_layout(
                title='Income vs Expenses Over Time',
                xaxis_title='Date',
                yaxis_title='Amount',
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Category-wise Expenses Pie Chart
        if st.session_state.transactions:
            expenses_by_category = {}
            for transaction in st.session_state.transactions:
                category = transaction['category']
                expenses_by_category[category] = expenses_by_category.get(category, 0) + transaction['amount']
            
            fig = px.pie(
                values=list(expenses_by_category.values()),
                names=list(expenses_by_category.keys()),
                title="Expenses by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Financial Trends
        st.subheader("Financial Trends")
        
        # Monthly Trend Analysis
        if st.session_state.income or st.session_state.transactions:
            monthly_data = []
            for transaction in st.session_state.transactions + st.session_state.income:
                date = pd.to_datetime(transaction['date'])
                monthly_data.append({
                    'month': date.strftime('%Y-%m'),
                    'type': transaction['type'],
                    'amount': transaction['amount']
                })
            
            if monthly_data:
                df = pd.DataFrame(monthly_data)
                monthly_summary = df.pivot_table(
                    values='amount',
                    index='month',
                    columns='type',
                    aggfunc='sum'
                ).fillna(0)
                
                fig = go.Figure()
                for col in monthly_summary.columns:
                    fig.add_trace(go.Scatter(
                        x=monthly_summary.index,
                        y=monthly_summary[col],
                        name=col,
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    title='Monthly Income vs Expenses Trend',
                    xaxis_title='Month',
                    yaxis_title='Amount'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Investment Performance Trend
        if st.session_state.investments:
            investment_data = []
            for investment in st.session_state.investments:
                if investment['type'] == 'Stocks':
                    try:
                        stock = yf.Ticker(investment['symbol'])
                        hist = stock.history(period="1y")
                        investment_data.append({
                            'symbol': investment['symbol'],
                            'data': hist['Close']
                        })
                    except:
                        st.warning(f"Could not fetch data for {investment['symbol']}")
            
            if investment_data:
                fig = go.Figure()
                for stock in investment_data:
                    fig.add_trace(go.Scatter(
                        x=stock['data'].index,
                        y=stock['data'].values,
                        name=stock['symbol'],
                        mode='lines'
                    ))
                
                fig.update_layout(
                    title='Stock Performance Over Time',
                    xaxis_title='Date',
                    yaxis_title='Price'
                )
                st.plotly_chart(fig, use_container_width=True)

elif page == "Transactions":
    st.subheader("Add Transaction")
    with st.form("transaction_form"):
        transaction_type = st.selectbox("Type", ["Income", "Expense"])
        amount = st.number_input("Amount", min_value=0.0)
        category = st.selectbox("Category", ["Salary", "Freelance", "Investments", "Food", "Transport", "Housing", "Entertainment", "Utilities", "Other"])
        description = st.text_input("Description")
        date = st.date_input("Date")
        
        if st.form_submit_button("Add Transaction"):
            transaction = {
                "type": transaction_type,
                "amount": amount,
                "category": category,
                "description": description,
                "date": date
            }
            if transaction_type == "Income":
                st.session_state.income.append(transaction)
            else:
                st.session_state.transactions.append(transaction)
            st.success("Transaction added successfully!")
    
    # Display Transactions
    st.subheader("Recent Transactions")
    all_transactions = st.session_state.income + st.session_state.transactions
    if all_transactions:
        df = pd.DataFrame(all_transactions)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)
        st.dataframe(df)
    else:
        st.info("No transactions yet. Add some transactions to get started!")

elif page == "Investments":
    st.subheader("Add Investment")
    with st.form("investment_form"):
        investment_type = st.selectbox("Type", INVESTMENT_CATEGORIES)
        amount = st.number_input("Amount", min_value=0.0)
        if investment_type == "Stocks":
            symbol = st.text_input("Stock Symbol (e.g., AAPL)")
        else:
            symbol = ""
        purchase_date = st.date_input("Purchase Date")
        
        if st.form_submit_button("Add Investment"):
            investment = {
                "type": investment_type,
                "amount": amount,
                "symbol": symbol,
                "purchase_date": purchase_date
            }
            st.session_state.investments.append(investment)
            st.success("Investment added successfully!")
    
    # Display Investments
    st.subheader("Investment Portfolio")
    if st.session_state.investments:
        df = pd.DataFrame(st.session_state.investments)
        df['purchase_date'] = pd.to_datetime(df['purchase_date'])
        st.dataframe(df)
        
        # Investment Performance Chart
        if any(inv['type'] == 'Stocks' for inv in st.session_state.investments):
            st.subheader("Stock Performance")
            stock_data = []
            for investment in st.session_state.investments:
                if investment['type'] == 'Stocks':
                    try:
                        stock = yf.Ticker(investment['symbol'])
                        hist = stock.history(period="1y")
                        stock_data.append({
                            'symbol': investment['symbol'],
                            'data': hist['Close']
                        })
                    except:
                        st.warning(f"Could not fetch data for {investment['symbol']}")
            
            if stock_data:
                fig = go.Figure()
                for stock in stock_data:
                    fig.add_trace(go.Scatter(
                        x=stock['data'].index,
                        y=stock['data'].values,
                        name=stock['symbol']
                    ))
                st.plotly_chart(fig)
    else:
        st.info("No investments yet. Add some investments to get started!")

elif page == "Debts":
    st.subheader("Add Debt")
    with st.form("debt_form"):
        debt_type = st.selectbox("Type", DEBT_CATEGORIES)
        amount = st.number_input("Amount", min_value=0.0)
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=100.0)
        term_months = st.number_input("Term (months)", min_value=1)
        
        if st.form_submit_button("Add Debt"):
            debt = {
                "type": debt_type,
                "amount": amount,
                "interest_rate": interest_rate,
                "term_months": term_months
            }
            st.session_state.debts.append(debt)
            st.success("Debt added successfully!")
    
    # Display Debts
    st.subheader("Debt Overview")
    if st.session_state.debts:
        df = pd.DataFrame(st.session_state.debts)
        st.dataframe(df)
        
        # Debt Payment Schedule
        for debt in st.session_state.debts:
            st.subheader(f"Payment Schedule for {debt['type']}")
            schedule = calculate_debt_payment_schedule(debt)
            schedule_df = pd.DataFrame(schedule)
            st.dataframe(schedule_df)
            
            # Payment Schedule Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=schedule_df['month'],
                y=schedule_df['balance'],
                name='Remaining Balance'
            ))
            st.plotly_chart(fig)
    else:
        st.info("No debts recorded. Add some debts to get started!")

elif page == "Goals":
    st.subheader("Add Financial Goal")
    with st.form("goal_form"):
        goal_name = st.text_input("Goal Name")
        target_amount = st.number_input("Target Amount", min_value=0.0)
        current_amount = st.number_input("Current Amount", min_value=0.0)
        target_date = st.date_input("Target Date")
        category = st.selectbox("Category", GOAL_CATEGORIES)
        
        if st.form_submit_button("Add Goal"):
            goal = {
                "name": goal_name,
                "target_amount": target_amount,
                "current_amount": current_amount,
                "target_date": target_date,
                "category": category
            }
            st.session_state.goals.append(goal)
            st.success("Goal added successfully!")
    
    # Display Goals
    st.subheader("Financial Goals")
    if st.session_state.goals:
        for goal in st.session_state.goals:
            progress = calculate_goal_progress(goal)
            st.write(f"**{goal['name']}** ({goal['category']})")
            st.progress(progress)
            st.write(f"Progress: {format_currency(goal['current_amount'])} / {format_currency(goal['target_amount'])}")
            st.write(f"Target Date: {goal['target_date']}")
            st.write("---")
    else:
        st.info("No financial goals set. Add some goals to get started!")

elif page == "Bills":
    st.subheader("Add Bill")
    with st.form("bill_form"):
        bill_name = st.text_input("Bill Name")
        amount = st.number_input("Amount", min_value=0.0)
        due_date = st.date_input("Due Date")
        frequency = st.selectbox("Frequency", ["Monthly", "Quarterly", "Yearly", "One-time"])
        category = st.selectbox("Category", ["Utilities", "Insurance", "Rent", "Mortgage", "Other"])
        
        if st.form_submit_button("Add Bill"):
            bill = {
                "name": bill_name,
                "amount": amount,
                "due_date": due_date,
                "frequency": frequency,
                "category": category
            }
            st.session_state.bills.append(bill)
            st.success("Bill added successfully!")
    
    # Display Bills
    st.subheader("Upcoming Bills")
    if st.session_state.bills:
        df = pd.DataFrame(st.session_state.bills)
        df['due_date'] = pd.to_datetime(df['due_date'])
        df = df.sort_values('due_date')
        st.dataframe(df)
        
        # Bills Timeline
        fig = go.Figure()
        for bill in st.session_state.bills:
            fig.add_trace(go.Scatter(
                x=[bill['due_date']],
                y=[bill['amount']],
                mode='markers+text',
                name=bill['name'],
                text=[bill['name']],
                textposition="top center",
            ))
        st.plotly_chart(fig)
    else:
        st.info("No bills recorded. Add some bills to get started!")

elif page == "Reports":
    st.subheader("Financial Reports")
    
    # Export Data
    if st.button("Export Data"):
        data = {
            "transactions": st.session_state.transactions,
            "income": st.session_state.income,
            "investments": st.session_state.investments,
            "debts": st.session_state.debts,
            "goals": st.session_state.goals,
            "bills": st.session_state.bills
        }
        json_str = json.dumps(data, default=str)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="finance_data.json",
            mime="application/json"
        )
    
    # Import Data
    uploaded_file = st.file_uploader("Import Data (JSON)", type=['json'])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.transactions = data.get("transactions", [])
            st.session_state.income = data.get("income", [])
            st.session_state.investments = data.get("investments", [])
            st.session_state.debts = data.get("debts", [])
            st.session_state.goals = data.get("goals", [])
            st.session_state.bills = data.get("bills", [])
            st.success("Data imported successfully!")
        except:
            st.error("Error importing data. Please check the file format.")
    
    # Generate Reports
    if st.button("Generate Monthly Report"):
        # Monthly Income vs Expenses
        monthly_data = []
        for transaction in st.session_state.transactions + st.session_state.income:
            date = pd.to_datetime(transaction['date'])
            monthly_data.append({
                'month': date.strftime('%Y-%m'),
                'type': transaction['type'],
                'amount': transaction['amount']
            })
        
        if monthly_data:
            df = pd.DataFrame(monthly_data)
            monthly_summary = df.pivot_table(
                values='amount',
                index='month',
                columns='type',
                aggfunc='sum'
            ).fillna(0)
            
            fig = go.Figure()
            for col in monthly_summary.columns:
                fig.add_trace(go.Bar(
                    x=monthly_summary.index,
                    y=monthly_summary[col],
                    name=col
                ))
            st.plotly_chart(fig)
        
        # Category-wise Expenses
        expenses_by_category = {}
        for transaction in st.session_state.transactions:
            category = transaction['category']
            expenses_by_category[category] = expenses_by_category.get(category, 0) + transaction['amount']
        
        if expenses_by_category:
            fig = px.pie(
                values=list(expenses_by_category.values()),
                names=list(expenses_by_category.keys()),
                title="Expenses by Category"
            )
            st.plotly_chart(fig)
        
        # Investment Performance
        if st.session_state.investments:
            investment_summary = {}
            for investment in st.session_state.investments:
                category = investment['type']
                investment_summary[category] = investment_summary.get(category, 0) + investment['amount']
            
            fig = px.pie(
                values=list(investment_summary.values()),
                names=list(investment_summary.keys()),
                title="Investment Portfolio Distribution"
            )
            st.plotly_chart(fig)
        
        # Debt Summary
        if st.session_state.debts:
            debt_summary = {}
            for debt in st.session_state.debts:
                category = debt['type']
                debt_summary[category] = debt_summary.get(category, 0) + debt['amount']
            
            fig = px.pie(
                values=list(debt_summary.values()),
                names=list(debt_summary.keys()),
                title="Debt Distribution"
            )
            st.plotly_chart(fig)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit") 