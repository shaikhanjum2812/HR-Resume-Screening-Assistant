import streamlit as st

def main():
    st.title("HR Assistant - Test Configuration")
    st.write("If you can see this message, the Streamlit server is running correctly on port 5000!")

    # Add a simple interactive element to test functionality
    if st.button("Click me!"):
        st.success("Button clicked successfully!")

if __name__ == "__main__":
    main()