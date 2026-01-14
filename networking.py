
import queue
from typing import Dict, Any

class Network:
    def __init__(self, node_ids: list):
        self.nodes: Dict[str, queue.Queue] = {node_id: queue.Queue() for node_id in node_ids}

    def send(self, recipient_id: str, message: Dict[str, Any]):
        """
        Sends a message to a specific node.
        """
        if recipient_id in self.nodes:
            self.nodes[recipient_id].put(message)

    def broadcast(self, sender_id: str, message: Dict[str, Any]):
        """
        Broadcasts a message to all other nodes in the network.
        """
        for node_id, node_queue in self.nodes.items():
            if node_id != sender_id:
                node_queue.put(message)

    def get_messages(self, node_id: str) -> queue.Queue:
        """
        Returns the message queue for a specific node.
        """
        return self.nodes.get(node_id, queue.Queue())
