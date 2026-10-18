from langchain_core.messages import HumanMessage

from src.app.infrastructure.llm import get_llm
from src.app.infrastructure.tools.registry import get_tools


def main():
    # Step 1: Load local model
    llm = get_llm()

    # Step 2: Load available tools
    tools = get_tools()

    # Step 3: Give tools to the model
    llm_with_tools = llm.bind_tools(tools)

    # Step 4: Ask a question that should trigger web search
    response = llm_with_tools.invoke(
        [
            HumanMessage(
                content="Search the web for the latest LangGraph documentation."
            )
        ]
    )

    # Step 5: Inspect the model's response
    print("\nAI Response:")
    print(response.content)

    print("\nTool Calls:")
    print(response.tool_calls)


if __name__ == "__main__":
    main()