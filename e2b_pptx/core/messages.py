from langchain_core.messages import ToolMessage

class RichToolMessage(ToolMessage):
    raw_output: dict 