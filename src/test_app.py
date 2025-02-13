import os
import streamlit as st

print("Starting Streamlit test app...")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {os.environ.get('PYTHONPATH')}")
print(f"Streamlit version: {st.__version__}")

try:
    st.title("HR Assistant")
    st.write("Welcome to the HR Assistant application!")

    if st.button("Click me to test interactivity"):
        st.success("Button clicked successfully!")
except Exception as e:
    print(f"Error in Streamlit app: {str(e)}")