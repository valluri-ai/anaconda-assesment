from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langgraph.graph import END, MessageGraph
from langgraph.prebuilt import ToolNode
from tools.presentation import create_presentation
from tools.yf_stocks import generate_python_dashboard
from core.prompts import SYSTEM_PROMPT

def should_continue(messages) -> str:
    """Determine if we should continue processing or end"""
    last_message = messages[-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return "end"
    return "continue"

def create_agent():
    print("\nCreating agent...")
    
    # Initialize LLM
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0,
        max_tokens=4000
    )
    
    # Create tools list
    tools = [create_presentation, generate_python_dashboard]
    
    # Create agent with tools
    agent = llm.bind_tools(tools) 
    
    # Create tool executor node
    tool_node = ToolNode(tools=tools)
    
    # Create workflow
    workflow = MessageGraph()
    
    # Add nodes
    workflow.add_node("agent", agent)
    workflow.add_node("tools", tool_node)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    print("Agent created successfully")
    return workflow.compile()