
import unittest
import threading
import time
from blockchain import Blockchain
from networking import Network
from pbft import PBFTNode

class TestPBFT(unittest.TestCase):

    def setUp(self):
        self.node_ids = ["node1", "node2", "node3", "node4"]
        self.network = Network(self.node_ids)
        self.nodes = {}
        for node_id in self.node_ids:
            blockchain = Blockchain()
            self.nodes[node_id] = PBFTNode(node_id, self.network, blockchain)

    def test_pbft_normal_case(self):
        # Start the nodes in separate threads
        threads = []
        for node in self.nodes.values():
            thread = threading.Thread(target=node.run, daemon=True)
            threads.append(thread)
            thread.start()

        # Let the primary node receive a request
        primary_node_id = self.nodes["node1"].get_primary()
        transaction = {"sender": "client", "recipient": "test", "amount": 10}
        request = {"type": "REQUEST", "transaction": transaction}
        self.network.send(primary_node_id, request)

        # Give the nodes time to process
        time.sleep(2)

        # Check if all nodes have committed the block
        final_block_hashes = [node.blockchain.last_block.hash for node in self.nodes.values()]
        self.assertEqual(len(set(final_block_hashes)), 1)
        self.assertEqual(self.nodes["node1"].blockchain.last_block.index, 1)

    def test_pbft_byzantine_fault(self):
        # One node is Byzantine (doesn't broadcast)
        byzantine_node_id = self.nodes["node1"].get_primary()

        class ByzantinePBFTNode(PBFTNode):
            def handle_request(self, message: dict):
                # This node is faulty and does not broadcast the PRE-PREPARE
                print(f"Node {self.node_id} (Byzantine) is dropping the request.")
                pass

        self.nodes[byzantine_node_id] = ByzantinePBFTNode(byzantine_node_id, self.network, self.nodes[byzantine_node_id].blockchain)


        # Start the nodes in separate threads
        threads = []
        for node in self.nodes.values():
            thread = threading.Thread(target=node.run, daemon=True)
            threads.append(thread)
            thread.start()

        # Let the primary node receive a request
        transaction = {"sender": "client", "recipient": "test", "amount": 10}
        request = {"type": "REQUEST", "transaction": transaction}
        self.network.send(byzantine_node_id, request)

        # Give the nodes time to process and trigger a view change
        time.sleep(self.nodes["node2"].timeout + 2)

        # The other nodes should have triggered a view change and elected a new primary
        self.assertGreater(self.nodes["node2"].view, 0)

        # A new request to the new primary should succeed
        new_primary_id = self.nodes["node2"].get_primary()
        self.network.send(new_primary_id, request)
        time.sleep(2)

        # Check if all honest nodes have committed the block
        honest_nodes = [node for node_id, node in self.nodes.items() if node_id != byzantine_node_id]
        final_block_hashes = [node.blockchain.last_block.hash for node in honest_nodes]
        self.assertEqual(len(set(final_block_hashes)), 1)
        self.assertEqual(self.nodes["node2"].blockchain.last_block.index, 1)

if __name__ == '__main__':
    unittest.main()
