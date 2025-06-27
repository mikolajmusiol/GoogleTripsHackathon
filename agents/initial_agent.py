from langchain_core.messages import ToolMessage, AIMessage, SystemMessage, HumanMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.schema import AgentState
from agents.tools import search_flights, get_hotels, get_local_attractions

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    api_key="AIzaSyDbCUYw6sdT2F92sfgg9Ht_8b9hbA6X3_w"
)
tools = [search_flights, get_hotels, get_local_attractions]
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState, config: RunnableConfig):
    """Invokes the LLM with the current message history."""
    response = llm_with_tools.invoke(state["messages"], config)
    return {"messages": [response]}

tool_node = ToolNode(tools)
def should_continue(state: AgentState) -> str:
    """
    Determines whether to continue with tool usage or end the current turn.

    Returns:
        "tools": If the model has requested to call one or more tools.
        "end": If the model has not requested tool usage, indicating a response to the user.
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"


def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("llm", call_model)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("llm")

    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    workflow.add_edge("tools", "llm")

    return workflow.compile()


if __name__ == "__main__":
    graph = create_graph()

    system_prompt = """
You are an AI Trip Assistant. Your primary goal is to help users plan comprehensive and personalized trips by using the tools available to you.

- First, understand the user's request. If any key details like destination, dates, or budget are missing, you MUST ask clarifying questions before using any tools.
- Once you have enough information, use the provided tools (`search_flights`, `get_hotels`, `get_local_attractions`) to gather the necessary data.
- After gathering information from the tools, synthesize it into a clear, helpful response for the user.
- You can use multiple tools in one turn if needed.
- Present the final plan or answer in a clean, readable format. Do not just output the raw tool results.
"""

    messages = [SystemMessage(content=system_prompt)]

    print("Hello! I am your AI Trip Assistant. How can I help you plan your trip today?")
    print("Type 'quit', 'exit', or 'q' to end the conversation.")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["quit", "exit", "q"]:
            break

        messages.append(HumanMessage(content=user_input))

        inputs = {"messages": messages}

        response = graph.invoke(inputs)

        final_agent_message = response["messages"][-1]

        print(f"\nAssistant: {final_agent_message.content}")

        messages = response["messages"]
