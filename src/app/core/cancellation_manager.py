import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


class CancellationManager:
    """Thread-safe registry for tracking and aborting active in-flight AI generation tasks."""

    def __init__(self) -> None:
        self._active_tasks: dict[uuid.UUID, asyncio.Task] = {}

    def register_task(self, conversation_id: uuid.UUID, task: asyncio.Task) -> None:
        """Associates an active asyncio Task with a conversation session."""
        self._active_tasks[conversation_id] = task
        logger.debug("Registered in-flight task for conversation: %s", conversation_id)

    def unregister_task(self, conversation_id: uuid.UUID) -> None:
        """Removes the task association once execution finishes or aborts."""
        self._active_tasks.pop(conversation_id, None)
        logger.debug("Unregistered in-flight task for conversation: %s", conversation_id)

    def abort_task(self, conversation_id: uuid.UUID) -> bool:
        """Instantly aborts the in-flight asyncio task for the given conversation.
        Returns True if an active task was found and cancelled, False otherwise.
        """
        task = self._active_tasks.get(conversation_id)
        if task and not task.done():
            task.cancel()
            logger.info("Aborted in-flight generation task immediately for conversation: %s", conversation_id)
            return True
        logger.debug("No active running task found to abort for conversation: %s", conversation_id)
        return False


cancellation_manager = CancellationManager()

