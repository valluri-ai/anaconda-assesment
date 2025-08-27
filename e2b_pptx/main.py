import os
from config.settings import OUTPUT_DIR
from ui.streamlit_app import init_streamlit_app

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initia+lize Streamlit app
    init_streamlit_app()

if __name__ == "__main__":
    main() 