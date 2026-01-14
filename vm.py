
from typing import List, Dict, Any

class VM:
    def __init__(self, gas_limit: int):
        self.stack: List[int] = []
        self.memory: Dict[int, int] = {}
        self.gas_limit = gas_limit
        self.gas_used = 0

    def use_gas(self, amount: int):
        """
        Consumes a specified amount of gas.
        """
        if self.gas_used + amount > self.gas_limit:
            raise Exception("Out of gas")
        self.gas_used += amount

    def execute(self, code: str) -> List[int]:
        """
        Executes smart contract bytecode.
        """
        opcodes = code.split()
        pc = 0
        while pc < len(opcodes):
            opcode = opcodes[pc]
            pc += 1

            self.use_gas(1) # Basic cost for any operation

            if opcode == "PUSH":
                self.stack.append(int(opcodes[pc]))
                pc += 1
            elif opcode == "POP":
                self.stack.pop()
            elif opcode == "ADD":
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append(a + b)
            elif opcode == "SUB":
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append(b - a)
            elif opcode == "MUL":
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append(a * b)
            elif opcode == "DIV":
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append(b // a)
            elif opcode == "STORE":
                addr = self.stack.pop()
                value = self.stack.pop()
                self.memory[addr] = value
                self.use_gas(5) # Higher cost for storage
            elif opcode == "LOAD":
                addr = self.stack.pop()
                self.stack.append(self.memory.get(addr, 0))
            else:
                raise Exception(f"Invalid opcode: {opcode}")

        return self.stack
