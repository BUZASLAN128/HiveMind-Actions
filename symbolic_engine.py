from __future__ import annotations
import math
import re
from typing import Union, Dict, List

class Expression:
    """Base class for all expressions in the symbolic math engine."""
    def simplify(self) -> Expression:
        """Simplify the expression."""
        return self

    def differentiate(self, var: str) -> Expression:
        raise NotImplementedError

    def integrate(self, var: str) -> Expression:
        raise NotImplementedError

    def __add__(self, other):
        return Operator('+', self, other)

    def __sub__(self, other):
        return Operator('-', self, other)

    def __mul__(self, other):
        return Operator('*', self, other)

    def __truediv__(self, other):
        return Operator('/', self, other)

    def __pow__(self, other):
        return Operator('^', self, other)

    def __eq__(self, other):
        return isinstance(other, Expression) and self.__dict__ == other.__dict__

class Constant(Expression):
    """Represents a constant value."""
    def __init__(self, value: Union[int, float]):
        self.value = float(value)

    def __repr__(self):
        return str(self.value)

    def differentiate(self, var: str) -> Expression:
        """Differentiate the constant."""
        return Constant(0)

    def integrate(self, var: str) -> Expression:
        """Integrate the constant."""
        return self * Variable(var)

class Variable(Expression):
    """Represents a variable."""
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name

    def differentiate(self, var: str) -> Expression:
        """Differentiate the variable."""
        return Constant(1) if self.name == var else Constant(0)

    def integrate(self, var: str) -> Expression:
        """Integrate the variable."""
        if self.name == var:
            return (self ** Constant(2)) / Constant(2)
        return self * Variable(var)

class Operator(Expression):
    """Represents an operator in an expression."""
    def __init__(self, op: str, left: Expression, right: Expression):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

    def simplify(self) -> Expression:
        left = self.left.simplify()
        right = self.right.simplify()
        op = self.op

        # Constant folding
        if isinstance(left, Constant) and isinstance(right, Constant):
            if op == '+': return Constant(left.value + right.value)
            if op == '-': return Constant(left.value - right.value)
            if op == '*': return Constant(left.value * right.value)
            if op == '/' and right.value != 0: return Constant(left.value / right.value)
            if op == '^': return Constant(left.value ** right.value)

        # Identity and dominant rules
        if op == '+' and isinstance(right, Constant) and right.value == 0: return left
        if op == '+' and isinstance(left, Constant) and left.value == 0: return right
        if op == '-' and isinstance(right, Constant) and right.value == 0: return left
        if op == '*' and isinstance(right, Constant) and right.value == 1: return left
        if op == '*' and isinstance(left, Constant) and left.value == 1: return right
        if op == '*' and (isinstance(right, Constant) and right.value == 0 or isinstance(left, Constant) and left.value == 0): return Constant(0)
        if op == '/' and isinstance(right, Constant) and right.value == 1: return left
        if op == '^' and isinstance(right, Constant) and right.value == 1: return left
        if op == '^' and isinstance(right, Constant) and right.value == 0: return Constant(1)
        if op == '^' and isinstance(left, Constant) and left.value == 1: return Constant(1)

        # Cancellation rules
        if op == '-' and left == right: return Constant(0)
        if op == '/' and left == right and not (isinstance(left, Constant) and left.value == 0): return Constant(1)

        # Re-association for constants
        # (a + c1) + c2 -> a + (c1 + c2)
        if op == '+' and isinstance(left, Operator) and left.op == '+' and isinstance(left.right, Constant) and isinstance(right, Constant):
            return (left.left + Constant(left.right.value + right.value)).simplify()
        # (a * c1) * c2 -> a * (c1 * c2)
        if op == '*' and isinstance(left, Operator) and left.op == '*' and isinstance(left.right, Constant) and isinstance(right, Constant):
            return (left.left * Constant(left.right.value * right.value)).simplify()
        # (c1 * a) * c2 -> (c1 * c2) * a
        if op == '*' and isinstance(left, Operator) and left.op == '*' and isinstance(left.left, Constant) and isinstance(right, Constant):
             return (Constant(left.left.value * right.value) * left.right).simplify()
        # (a + c1) - c2 -> a + (c1 - c2)
        if op == '-' and isinstance(left, Operator) and left.op == '+' and isinstance(left.right, Constant) and isinstance(right, Constant):
            return (left.left + Constant(left.right.value - right.value)).simplify()

        # (c1 * a) / c2 -> (c1 / c2) * a
        if op == '/' and isinstance(left, Operator) and left.op == '*' and isinstance(left.left, Constant) and isinstance(right, Constant) and right.value != 0:
            return (Constant(left.left.value / right.value) * left.right).simplify()

        # sin(x)^2 + cos(x)^2 = 1
        if op == '+' and isinstance(left, Operator) and left.op == '^' and isinstance(right, Operator) and right.op == '^':
            if isinstance(left.left, Function) and left.left.func == 'sin' and isinstance(right.left, Function) and right.left.func == 'cos':
                if left.left.arg == right.left.arg and isinstance(left.right, Constant) and left.right.value == 2 and isinstance(right.right, Constant) and right.right.value == 2:
                    return Constant(1)

        # Comining like terms c1*x + c2*x -> (c1+c2)*x
        if op == '+' and isinstance(left, Operator) and left.op == '*' and isinstance(right, Operator) and right.op == '*':
            if isinstance(left.left, Constant) and left.right == right.right:
                return (Constant(left.left.value + right.left.value) * left.right).simplify()
            if isinstance(left.right, Constant) and left.left == right.left:
                return (Constant(left.right.value + right.right.value) * left.left).simplify()

        # x + x -> 2*x
        if op == '+' and left == right:
            return (Constant(2) * left).simplify()

        # c * (x / c) -> x
        if op == '*' and isinstance(right, Operator) and right.op == '/' and isinstance(left, Constant) and isinstance(right.right, Constant) and left.value == right.right.value:
            return right.left.simplify()

        # Expansion of powers (a+b)^2 -> a^2 + 2ab + b^2
        if op == '^' and isinstance(left, Operator) and left.op == '+' and isinstance(right, Constant) and right.value == 2:
            a, b = left.left, left.right
            return (a**Constant(2) + Constant(2)*a*b + b**Constant(2)).simplify()

        # Factoring a^2 - b^2 -> (a-b)*(a+b)
        if op == '-' and isinstance(left, Operator) and left.op == '^' and isinstance(left.right, Constant) and left.right.value == 2:
            a = left.left
            if isinstance(right, Constant) and right.value == 1:
                b = Constant(1)
                return ((a - b).simplify() * (a + b).simplify()).simplify()
            if isinstance(right, Operator) and right.op == '^' and isinstance(right.right, Constant) and right.right.value == 2:
                b = right.left
                return ((a - b).simplify() * (a + b).simplify()).simplify()

        # Canceling common factors in fractions (a*b)/a -> b
        if op == '/' and isinstance(left, Operator) and left.op == '*':
            if left.left == right: return left.right.simplify()
            if left.right == right: return left.left.simplify()

        return Operator(op, left, right)

    def differentiate(self, var: str) -> Expression:
        left_deriv = self.left.differentiate(var)
        right_deriv = self.right.differentiate(var)

        if self.op == '+':
            return (left_deriv + right_deriv).simplify()
        if self.op == '-':
            return (left_deriv - right_deriv).simplify()
        if self.op == '*':
            return (self.left * right_deriv + left_deriv * self.right).simplify()
        if self.op == '/':
            return ((left_deriv * self.right - self.left * right_deriv) / (self.right ** Constant(2))).simplify()
        if self.op == '^':
            if isinstance(self.right, Constant):
                n = self.right
                return (n * (self.left ** Constant(n.value - 1)) * left_deriv).simplify()
            else:
                f, g = self.left, self.right
                return (f ** g * (g.differentiate(var) * Function('ln', f) + g * f.differentiate(var) / f)).simplify()

    def integrate(self, var: str) -> Expression:
        if self.op == '+':
            return (self.left.integrate(var) + self.right.integrate(var)).simplify()
        if self.op == '-':
            return (self.left.integrate(var) - self.right.integrate(var)).simplify()
        if self.op == '*' and isinstance(self.left, Constant):
            return (self.left * self.right.integrate(var)).simplify()
        if self.op == '*' and isinstance(self.right, Constant):
            return (self.right * self.left.integrate(var)).simplify()
        if self.op == '^':
            if isinstance(self.left, Variable) and self.left.name == var and isinstance(self.right, Constant):
                n = self.right.value
                return (self.left ** Constant(n + 1)) / Constant(n + 1)
            # (ax+b)^n
            if isinstance(self.left, Operator) and self.left.op == '+' and isinstance(self.right, Constant):
                n = self.right.value
                a, b = self.left.left, self.left.right
                if isinstance(a, Operator) and a.op == '*' and isinstance(a.left, Constant) and isinstance(a.right, Variable) and a.right.name == var and isinstance(b, Constant):
                    return ((self.left ** Constant(n + 1)) / (Constant(n + 1) * a.left)).simplify()

        raise NotImplementedError(f"Integration of {self.op} not implemented.")

class Function(Expression):
    """Represents a function in an expression."""
    def __init__(self, func: str, arg: Expression):
        self.func = func
        self.arg = arg

    def __repr__(self):
        return f"{self.func}({self.arg})"

    def simplify(self) -> Expression:
        arg = self.arg.simplify()
        if self.func == 'ln' and isinstance(arg, Function) and arg.func == 'exp':
            return arg.arg
        return Function(self.func, arg)

    def differentiate(self, var: str) -> Expression:
        arg_deriv = self.arg.differentiate(var)

        if self.func == 'sin':
            return (Function('cos', self.arg) * arg_deriv).simplify()
        if self.func == 'cos':
            return (Constant(-1) * Function('sin', self.arg) * arg_deriv).simplify()
        if self.func == 'tan':
            return (arg_deriv / (Function('cos', self.arg) ** Constant(2))).simplify()
        # log is treated as natural logarithm (ln)
        if self.func == 'ln' or self.func == 'log':
            return (arg_deriv / self.arg).simplify()
        if self.func == 'exp':
            return (Function('exp', self.arg) * arg_deriv).simplify()
        if self.func == 'sqrt':
            return (arg_deriv / (Constant(2) * Function('sqrt', self.arg))).simplify()

        raise NotImplementedError(f"Derivative of {self.func} not implemented.")

    def integrate(self, var: str) -> Expression:
        if isinstance(self.arg, Variable) and self.arg.name == var:
            if self.func == 'sin':
                return Constant(-1) * Function('cos', self.arg)
            if self.func == 'cos':
                return Function('sin', self.arg)
            if self.func == 'exp':
                return Function('exp', self.arg)
            # log is treated as natural logarithm (ln)
            if self.func == 'ln' or self.func == 'log':
                return self.arg * Function('ln', self.arg) - self.arg

        raise NotImplementedError(f"Integration of {self.func} not implemented.")

def parse(expression: str) -> Expression:
    token_regex = re.compile(r"(\d+\.?\d*|[a-zA-Z_][a-zA-Z0-9_]*|[+\-*/^()])")
    tokens = token_regex.findall(expression)

    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    associativity = {'+': 'L', '-': 'L', '*': 'L', '/': 'L', '^': 'R'}
    functions = {'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt', 'pi', 'e'}

    output = []
    operators = []

    prev_token = None
    for token in tokens:
        if token == '-' and (prev_token is None or prev_token in precedence or prev_token == '('):
            operators.append('unary-')
        elif token.replace('.', '', 1).isdigit():
            output.append(Constant(float(token)))
            prev_token = token
        elif token == 'pi':
            output.append(Constant(math.pi))
            prev_token = token
        elif token == 'e':
            output.append(Constant(math.e))
            prev_token = token
        elif token in functions:
            operators.append(token)
            prev_token = token
        elif token.isalpha():
            output.append(Variable(token))
            prev_token = token
        elif token in precedence:
            while (operators and operators[-1] in precedence and
                   ((associativity[token] == 'L' and precedence[token] <= precedence[operators[-1]]) or
                    (associativity[token] == 'R' and precedence[token] < precedence[operators[-1]]))):
                output.append(operators.pop())
            operators.append(token)
            prev_token = token
        elif token == '(':
            operators.append(token)
            prev_token = token
        elif token == ')':
            while operators and operators[-1] != '(':
                output.append(operators.pop())
            if not operators or operators.pop() != '(':
                raise ValueError("Mismatched parentheses")
            if operators and operators[-1] in functions:
                output.append(operators.pop())
            prev_token = token

    while operators:
        op = operators.pop()
        if op == '(':
            raise ValueError("Mismatched parentheses")
        output.append(op)

    stack = []
    for token in output:
        if isinstance(token, Expression):
            stack.append(token)
        elif token == 'unary-':
            if not stack:
                raise ValueError("Invalid expression")
            stack.append(Operator('*', Constant(-1), stack.pop()))
        elif token in functions:
            if not stack:
                raise ValueError("Invalid expression")
            stack.append(Function(token, stack.pop()))
        elif token in precedence:
            if len(stack) < 2:
                raise ValueError("Invalid expression")
            right = stack.pop()
            left = stack.pop()
            stack.append(Operator(token, left, right))

    if len(stack) != 1:
        raise ValueError("Invalid expression")

    return stack[0]
