import os
import streamlit as st
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from core.messages import RichToolMessage

def display_message(message: BaseMessage):
    print(f"\nDisplaying message of type: {type(message)}")
    if isinstance(message, AIMessage):
        st.write("AI: ", message.content)
        print(f"AI Message: {message.content}")
    elif isinstance(message, HumanMessage):
        st.write("Human: ", message.content)
        print(f"Human Message: {message.content}")
    elif isinstance(message, RichToolMessage):
        print("Processing RichToolMessage")
        if message.raw_output.get("results"):
            for result in message.raw_output["results"]:
                if isinstance(result, dict) and result.get("type") == "pptx_files":
                    for path in result["local_paths"]:
                        print(f"Creating download button for: {path}")
                        try:
                            with open(path, 'rb') as f:
                                file_data = f.read()
                                st.download_button(
                                    label=f"Download {os.path.basename(path)}",
                                    data=file_data,
                                    file_name=os.path.basename(path),
                                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                                )
                                print(f"Download button created successfully for {path}")
                        except Exception as e:
                            print(f"Error creating download button: {str(e)}")
                            st.error(f"Error loading file {path}: {str(e)}")
    