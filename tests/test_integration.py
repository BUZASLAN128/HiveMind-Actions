
import unittest
import threading
import time
from blockchain import Blockchain
from networking import Network
from pbft import PBFTNode

class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.node_ids = ["node1", "node2", "node3", "node4"]
        self.network = Network(self.node_ids)
        self.nodes = {}
        for node_id in self.node_ids:
            blockchain = Blockchain()
            self.nodes[node_id] = PBFTNode(node_id, self.network, blockchain)

    def test_smart_contract_execution(self):
        # Start the nodes in separate threads
        threads = []
        for node in self.nodes.values():
            thread = threading.Thread(target=node.run, daemon=True)
            threads.append(thread)
            thread.start()

        # A smart contract that pushes 2 and 3, then adds them
        contract_code = "PUSH 2 PUSH 3 ADD"

        # Let the primary node receive a request
        primary_node_id = self.nodes["node1"].get_primary()
        transaction = {
            "sender": "client",
            "recipient": "contract",
            "amount": 0,
            "contract_code": contract_code,
            "gas_limit": 100
        }
        request = {"type": "REQUEST", "transaction": transaction}
        self.network.send(primary_node_id, request)

        # Give the nodes time to process
        time.sleep(2)

        # Check if all nodes have committed the block with the smart contract
        final_block_hashes = [node.blockchain.last_block.hash for node in self.nodes.values()]
        self.assertEqual(len(set(final_block_hashes)), 1)

        last_block = self.nodes["node1"].blockchain.last_block
        self.assertEqual(len(last_block.transactions), 1)
        self.assertEqual(last_block.transactions[0]["contract_code"], contract_code)

if __name__ == '__main__':
    unittest.main()
