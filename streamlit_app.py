import streamlit as st
import subprocess
import time
import atexit

# Path to your Flask app
flask_app_path = 'app.py'

# Function to start Flask app
def start_flask():
    return subprocess.Popen(['python', flask_app_path])

# Start the Flask app
flask_process = start_flask()

# Register the function to stop the Flask app at exit
atexit.register(lambda: flask_process.terminate())

# Wait for Flask server to start
time.sleep(1)  # Adjust this time if needed

# Set the page title and icon
st.set_page_config(
    page_title="Resume Keyword Search",
    page_icon="https://indiatechnologynews.in/wp-content/uploads/2021/09/nxt-wave.png"
)

# Create an iframe to embed the Flask app
st.markdown('''
    <style>
    .full-screen-frame {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
        margin: 0;
        padding: 0;
        overflow: hidden;
        z-index: 999999;
    }
    </style>
    <iframe src="http://localhost:8000" class="full-screen-frame"></iframe>
''', unsafe_allow_html=True)
