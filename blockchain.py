
import hashlib
import json
from time import time
from typing import List, Dict, Any

class Block:
    def __init__(self, index: int, transactions: List[Dict[str, Any]], timestamp: float, previous_hash: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculates the SHA-256 hash of the block by creating a deterministic JSON string.
        """
        # Convert transaction dicts to sorted JSON strings to ensure deterministic hashing
        sorted_transactions = [json.dumps(tx, sort_keys=True) for tx in self.transactions]

        block_dict = {
            "index": self.index,
            "transactions": sorted_transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }

        block_string = json.dumps(block_dict, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the block.
        """
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Creates the very first block in the chain.
        """
        genesis_block = Block(0, [], 0, "0")
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        """
        Returns the last block in the chain.
        """
        return self.chain[-1]

    def add_block(self, block: Block) -> bool:
        """
        Adds a new block to the chain after verifying it.
        """
        if self.is_valid_block(block, self.last_block):
            self.chain.append(block)
            return True
        return False

    def is_valid_block(self, block: Block, previous_block: Block) -> bool:
        """
        Checks if a block is valid.
        """
        if previous_block.index + 1 != block.index:
            return False
        if previous_block.hash != block.previous_hash:
            return False
        if block.calculate_hash() != block.hash:
            return False
        return True

    @staticmethod
    def merkle_tree(transactions: List[Dict[str, Any]]) -> str:
        """
        Computes the Merkle root of a list of transactions.
        """
        if not transactions:
            return hashlib.sha256(b"").hexdigest()

        transaction_hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() for tx in transactions]

        while len(transaction_hashes) > 1:
            if len(transaction_hashes) % 2 != 0:
                transaction_hashes.append(transaction_hashes[-1])

            new_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                combined_hash = hashlib.sha256((transaction_hashes[i] + transaction_hashes[i+1]).encode()).hexdigest()
                new_hashes.append(combined_hash)
            transaction_hashes = new_hashes

        return transaction_hashes[0]
