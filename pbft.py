
import queue
import threading
import json
import hashlib
from typing import Dict, Any, List
from time import time
from collections import defaultdict

from blockchain import Blockchain, Block
from networking import Network
from vm import VM

class PBFTNode:
    def __init__(self, node_id: str, network: Network, blockchain: Blockchain):
        self.node_id = node_id
        self.network = network
        self.blockchain = blockchain
        self.view = 0
        self.sequence_number = 0
        self.timeout = 5  # seconds
        self.f = (len(network.nodes) - 1) // 3
        self.lock = threading.Lock()

        self.pre_prepare_log: Dict[int, Dict[str, Any]] = {}
        self.prepare_log: Dict[int, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self.commit_log: Dict[int, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self.request_log: Dict[str, Dict[str, Any]] = {}

        self.is_primary = self.node_id == self.get_primary()

    def get_primary(self) -> str:
        """
        Determines the primary node for the current view.
        """
        primaries = sorted(self.network.nodes.keys())
        return primaries[self.view % len(primaries)]

    def run(self):
        """
        The main loop for the PBFT node.
        """
        while True:
            try:
                message = self.network.get_messages(self.node_id).get(timeout=self.timeout)
                self.handle_message(message)
            except queue.Empty:
                self.handle_timeout()

    def handle_message(self, message: Dict[str, Any]):
        """
        Routes incoming messages to the appropriate handler.
        """
        with self.lock:
            msg_type = message.get("type")
            if msg_type == "REQUEST":
                self.handle_request(message)
            elif msg_type == "PRE-PREPARE":
                self.handle_pre_prepare(message)
            elif msg_type == "PREPARE":
                self.handle_prepare(message)
            elif msg_type == "COMMIT":
                self.handle_commit(message)
            elif msg_type == "VIEW-CHANGE":
                self.handle_view_change(message)

    def handle_request(self, message: Dict[str, Any]):
        """
        Handles a new transaction request from a client.
        """
        if self.is_primary:
            self.sequence_number += 1
            request_digest = hashlib.sha256(json.dumps(message["transaction"], sort_keys=True).encode()).hexdigest()
            self.request_log[request_digest] = message

            timestamp = time()
            pre_prepare_message = {
                "type": "PRE-PREPARE",
                "view": self.view,
                "seq_num": self.sequence_number,
                "digest": request_digest,
                "transaction": message["transaction"],
                "timestamp": timestamp
            }
            self.pre_prepare_log[self.sequence_number] = pre_prepare_message
            self.network.broadcast(self.node_id, pre_prepare_message)

    def handle_pre_prepare(self, message: Dict[str, Any]):
        """
        Handles a PRE-PREPARE message from the primary.
        """
        if message["view"] == self.view and message["seq_num"] > self.sequence_number:
            self.sequence_number = message["seq_num"]
            self.pre_prepare_log[message["seq_num"]] = message

            prepare_message = {
                "type": "PREPARE",
                "view": self.view,
                "seq_num": message["seq_num"],
                "digest": message["digest"],
                "sender": self.node_id
            }
            self.network.broadcast(self.node_id, prepare_message)

    def handle_prepare(self, message: Dict[str, Any]):
        """
        Handles a PREPARE message from a replica.
        """
        seq_num = message["seq_num"]
        digest = message["digest"]
        sender = message["sender"]

        if message["view"] == self.view and seq_num in self.pre_prepare_log:
            self.prepare_log[seq_num][digest].append(sender)

            if len(self.prepare_log[seq_num][digest]) >= 2 * self.f:
                commit_message = {
                    "type": "COMMIT",
                    "view": self.view,
                    "seq_num": seq_num,
                    "digest": digest,
                    "sender": self.node_id
                }
                self.network.broadcast(self.node_id, commit_message)

    def handle_commit(self, message: Dict[str, Any]):
        """
        Handles a COMMIT message from a replica.
        """
        seq_num = message["seq_num"]
        digest = message["digest"]
        sender = message["sender"]

        if message["view"] == self.view and seq_num in self.pre_prepare_log:
            self.commit_log[seq_num][digest].append(sender)

            if len(self.commit_log[seq_num][digest]) >= 2 * self.f + 1:
                self.execute_committed(seq_num)

    def execute_committed(self, seq_num: int):
        """
        Executes a committed transaction and adds it to the blockchain.
        """
        # By popping the message, we ensure that we only execute this once
        # for a given sequence number, preventing race conditions.
        pre_prepare_message = self.pre_prepare_log.pop(seq_num, None)
        if not pre_prepare_message:
            return

        transaction = pre_prepare_message["transaction"]

        if transaction.get("contract_code"):
            vm = VM(gas_limit=transaction["gas_limit"])
            try:
                vm.execute(transaction["contract_code"])
            except Exception as e:
                print(f"Node {self.node_id}: VM execution failed: {e}")
                return

        new_block = Block(
            index=len(self.blockchain.chain),
            transactions=[transaction],
            timestamp=pre_prepare_message["timestamp"],
            previous_hash=self.blockchain.last_block.hash
        )
        self.blockchain.add_block(new_block)
        print(f"Node {self.node_id}: Block #{new_block.index} committed.")

    def handle_timeout(self):
        """
        Handles a view change when a timeout occurs.
        """
        self.view += 1
        self.is_primary = self.node_id == self.get_primary()

        view_change_message = {
            "type": "VIEW-CHANGE",
            "view": self.view,
            "sender": self.node_id
        }
        self.network.broadcast(self.node_id, view_change_message)
        print(f"Node {self.node_id}: Timeout, starting view change to {self.view}")

    def handle_view_change(self, message: Dict[str, Any]):
        # Basic view change logic
        # A full implementation would require collecting view-change messages
        # and the new primary sending a NEW-VIEW message.
        if message["view"] > self.view:
            self.view = message["view"]
            self.is_primary = self.node_id == self.get_primary()
            print(f"Node {self.node_id}: View changed to {self.view}")
