import streamlit as st
from langchain_core.messages import SystemMessage, HumanMessage
from core.agent import create_agent
from core.prompts import SYSTEM_PROMPT
from utils.display import display_message

def init_streamlit_app():
    st.title("PowerPoint Presentation Generator")
    
    if "agent" not in st.session_state:
        st.session_state.agent = create_agent()

    if prompt := st.chat_input("What kind of presentation would you like to create?"):
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        with st.spinner("Creating your presentation..."):
            for message in st.session_state.agent.stream(messages):
                st.write(message)
                display_message(message)
                if "end" in message:
                    st.write(message)
            