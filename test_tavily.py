from src.app.infrastructure.tools.search import get_search_tool


def main():
    search_tool = get_search_tool()

    result = search_tool.invoke(
        {
            "query": "Latest LangGraph documentation"
        }
    )

    print(result)


if __name__ == "__main__":
    main()