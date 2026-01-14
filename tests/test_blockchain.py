
import unittest
from blockchain import Block, Blockchain
from time import time

class TestBlockchain(unittest.TestCase):

    def test_block_creation(self):
        block = Block(0, [], time(), "0")
        self.assertEqual(block.index, 0)
        self.assertEqual(block.previous_hash, "0")
        self.assertIsNotNone(block.hash)

    def test_blockchain_creation(self):
        blockchain = Blockchain()
        self.assertEqual(len(blockchain.chain), 1)
        self.assertEqual(blockchain.chain[0].index, 0)

    def test_add_block(self):
        blockchain = Blockchain()
        previous_block = blockchain.last_block
        new_block = Block(1, [], time(), previous_block.hash)
        self.assertTrue(blockchain.add_block(new_block))
        self.assertEqual(len(blockchain.chain), 2)
        self.assertEqual(blockchain.last_block.index, 1)

    def test_invalid_block(self):
        blockchain = Blockchain()
        previous_block = blockchain.last_block
        # Invalid index
        invalid_block_1 = Block(2, [], time(), previous_block.hash)
        self.assertFalse(blockchain.add_block(invalid_block_1))
        # Invalid previous_hash
        invalid_block_2 = Block(1, [], time(), "invalid_hash")
        self.assertFalse(blockchain.add_block(invalid_block_2))

    def test_merkle_tree(self):
        transactions = [
            {"sender": "a", "recipient": "b", "amount": 1},
            {"sender": "b", "recipient": "c", "amount": 2},
            {"sender": "c", "recipient": "d", "amount": 3}
        ]
        merkle_root = Blockchain.merkle_tree(transactions)
        self.assertIsInstance(merkle_root, str)
        self.assertEqual(len(merkle_root), 64)

if __name__ == '__main__':
    unittest.main()
