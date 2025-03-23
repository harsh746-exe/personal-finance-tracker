import streamlit as st
import pandas as pd
import numpy as np

# Set page title
st.title("My First Streamlit App")

# Add some text
st.write("Welcome to this interactive app!")

# Create a slider
number = st.slider("Pick a number", 0, 100, 50)
st.write(f"Your number is: {number}")

# Create a text input
user_input = st.text_input("Enter your name", "")
if user_input:
    st.write(f"Hello, {user_input}!")

# Create a simple chart
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)
st.line_chart(chart_data)

# Add a selectbox
option = st.selectbox(
    'What is your favorite color?',
    ['Red', 'Green', 'Blue']
)
st.write(f'Your favorite color is {option}')

# Add a checkbox
if st.checkbox('Show more options'):
    st.write("Here are some additional options!")
    st.multiselect(
        'Select multiple items',
        ['Item 1', 'Item 2', 'Item 3', 'Item 4']
    ) 