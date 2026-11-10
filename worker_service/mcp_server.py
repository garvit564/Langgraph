import logging
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from tavily import TavilyClient
from worker_service.config import get_worker_settings
from worker_service.tasks.email_tasks import send_email_task

logger = logging.getLogger(__name__)
settings = get_worker_settings()

# Official FastMCP Server instance hosted on Port 8001
# DNS rebinding protection disabled so tunnels (ngrok, cloudflare) and external hosts can connect
tools_mcp = FastMCP(
    "AgentToolsMCPServer",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@tools_mcp.tool(
    name="send_email",
    description="Sends an email to a specified recipient asynchronously via background Celery worker. Use this whenever the user asks to email, dispatch, or forward information, reports, or contact lists.",
)
def send_email(to_email: str, subject: str, body: str) -> str:
    """Queues an email delivery task directly to the Celery broker over Redis."""
    logger.info("FastMCP 'send_email' invoked for recipient: %s", to_email)
    try:
        task = send_email_task.delay(
            to_email=to_email,
            subject=subject,
            body=body,
        )
        logger.info("Enqueued task %s via MCP to Celery broker", task.id)
        return f"Email queued successfully for delivery to {to_email}. Background Task ID: {task.id}"
    except Exception as exc:
        logger.exception("Failed to dispatch task from MCP to Celery: %s", exc)
        return f"Failed to queue email task: {str(exc)}"


@tools_mcp.tool(
    name="web_search",
    description="Search the web for current information, recent news, documentation, and facts that require online research.",
)
def web_search(query: str) -> dict:
    """Performs live web research via the Tavily Search engine."""
    logger.info("FastMCP 'web_search' invoked for query: '%s'", query)
    try:
        if not settings.tavily_api_key:
            return {"error": "Tavily API key is not configured in Worker service."}
        client = TavilyClient(api_key=settings.tavily_api_key)
        results = client.search(query=query, max_results=5, topic="general")
        return results
    except Exception as exc:
        logger.exception("Failed to execute Tavily search via MCP: %s", exc)
        return {"error": f"Search failed: {str(exc)}"}


# Alias for compatibility
email_mcp = tools_mcp


if __name__ == "__main__":
    tools_mcp.run()

