import streamlit as st

def home():
    st.title("Welcome to My Streamlit App")
    st.write("This is the home page of the application.")
    
    st.header("About This App")
    st.write("This app is designed to demonstrate the capabilities of Streamlit.")
    
    st.header("Features")
    st.write("- Interactive data visualizations")
    st.write("- Easy navigation between pages")
    st.write("- User-friendly interface")
    
    st.header("Get Started")
    st.write("Use the sidebar to navigate to different sections of the app.")
    
if __name__ == "__main__":
    home()