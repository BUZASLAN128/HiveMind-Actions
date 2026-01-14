
import unittest
from vm import VM

class TestVM(unittest.TestCase):

    def test_push_pop(self):
        vm = VM(gas_limit=100)
        vm.execute("PUSH 10 PUSH 20 POP")
        self.assertEqual(vm.stack, [10])

    def test_arithmetic(self):
        vm = VM(gas_limit=100)
        vm.execute("PUSH 10 PUSH 20 ADD")
        self.assertEqual(vm.stack, [30])
        vm.execute("PUSH 5 PUSH 3 SUB")
        self.assertEqual(vm.stack, [30, 2])
        vm.execute("PUSH 4 MUL")
        self.assertEqual(vm.stack, [30, 8])
        vm.execute("PUSH 2 DIV")
        self.assertEqual(vm.stack, [30, 4])


    def test_storage(self):
        vm = VM(gas_limit=100)
        vm.execute("PUSH 100 PUSH 42 STORE")
        self.assertEqual(vm.memory[42], 100)
        vm.execute("PUSH 42 LOAD")
        self.assertEqual(vm.stack, [100])

    def test_out_of_gas(self):
        vm = VM(gas_limit=5)
        with self.assertRaises(Exception) as context:
            vm.execute("PUSH 1 PUSH 2 ADD PUSH 3 STORE")
        self.assertTrue("Out of gas" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
