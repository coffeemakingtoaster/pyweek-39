from panda3d.core import NodePath
import logging

LOGGER = logging.getLogger(__name__)

def traverse_parents_until_name_is_matched(start_node_path: NodePath, target_name: str) -> NodePath | None:
    while not start_node_path.is_empty():
        if start_node_path.getName() == target_name:
            return start_node_path
        start_node_path = start_node_path.getParent()
    LOGGER.error(f"Could not find any parent with name {target_name}")
    return None
