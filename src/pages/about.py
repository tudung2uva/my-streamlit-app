import streamlit as st

def about():
    st.title("About This Application")
    st.write("""
        This application is designed to provide users with insights and visualizations based on the data provided.
        
        ## Purpose
        The main goal of this app is to demonstrate the capabilities of Streamlit for building interactive web applications for data science and machine learning projects.
        
        ## How to Use
        - Navigate to the **Home** page to view the main features of the application.
        - Use the sidebar to access different sections of the app.
        
        ## Contact
        For any inquiries or feedback, please reach out to the development team.
    """)

if __name__ == "__main__":
    about()