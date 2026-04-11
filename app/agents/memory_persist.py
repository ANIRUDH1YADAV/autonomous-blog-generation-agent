import logging

logger = logging.getLogger(__name__)


def memory_persist_node(state: dict) -> dict:
    """
    Explicit workflow step for memory persistence.
    AsyncSqliteSaver checkpoints every node transition into memory.db.
    """
    logger.info("Memory persistence step complete via AsyncSqliteSaver checkpoints")
    return {"saved_to_memory": True}
