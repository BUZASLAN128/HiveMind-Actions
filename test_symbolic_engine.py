import unittest
import math
from symbolic_engine import parse

def numerical_derivative(expr, var, at, h=1e-6):

    def evaluate(expression, **kwargs):
        if 'value' in expression.__dict__:
            return expression.value
        if 'name' in expression.__dict__:
            return kwargs.get(expression.name, 0)

        if 'func' in expression.__dict__:
            arg = evaluate(expression.arg, **kwargs)
            if expression.func == 'sin': return math.sin(arg)
            if expression.func == 'cos': return math.cos(arg)
            if expression.func == 'ln': return math.log(arg)
            if expression.func == 'exp': return math.exp(arg)
            if expression.func == 'sqrt': return math.sqrt(arg)
            if expression.func == 'tan': return math.tan(arg)
            if expression.func == 'log': return math.log(arg)

        left = evaluate(expression.left, **kwargs)
        right = evaluate(expression.right, **kwargs)

        if expression.op == '+': return left + right
        if expression.op == '-': return left - right
        if expression.op == '*': return left * right
        if expression.op == '/': return left / right
        if expression.op == '^': return left ** right

        raise ValueError(f"Unknown operator: {expression.op}")

    return (evaluate(expr, **{var: at + h}) - evaluate(expr, **{var: at - h})) / (2 * h)

class TestSymbolicEngine(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(repr(parse("x + 1")), "(x + 1.0)")
        self.assertEqual(repr(parse("2 * (x + 1)")), "(2.0 * (x + 1.0))")
        self.assertEqual(repr(parse("sin(x^2)")), "sin((x ^ 2.0))")
        self.assertEqual(repr(parse("ln(exp(x))")), "ln(exp(x))")
        self.assertEqual(repr(parse("-x")), "(-1.0 * x)")

    def test_simplification(self):
        self.assertEqual(repr(parse("x+0").simplify()), "x")
        self.assertEqual(repr(parse("0+x").simplify()), "x")
        self.assertEqual(repr(parse("x*1").simplify()), "x")
        self.assertEqual(repr(parse("1*x").simplify()), "x")
        self.assertEqual(repr(parse("x*0").simplify()), "0.0")
        self.assertEqual(repr(parse("0*x").simplify()), "0.0")
        self.assertEqual(repr(parse("x^1").simplify()), "x")
        self.assertEqual(repr(parse("2+2").simplify()), "4.0")
        self.assertEqual(repr(parse("2*3").simplify()), "6.0")
        self.assertEqual(repr(parse("ln(exp(x))").simplify()), "x")
        self.assertEqual(repr(parse("(x+0)*1").simplify()), "x")
        self.assertEqual(repr(parse("x+1+2").simplify()), "(x + 3.0)")
        self.assertEqual(repr(parse("x*2*3").simplify()), "(x * 6.0)")
        self.assertEqual(repr(parse("(x+1-1)").simplify()), "x")
        self.assertEqual(repr(parse("x/1").simplify()), "x")
        self.assertEqual(repr(parse("(x^2)/x").simplify()), "((x ^ 2.0) / x)")
        self.assertEqual(repr(parse("sin(x)^2+cos(x)^2").simplify()), "1.0")
        self.assertEqual(repr(parse("2*x + 3*x").simplify()), "(5.0 * x)")
        self.assertEqual(repr(parse("(x+1)^2").simplify()), "(((x ^ 2.0) + (2.0 * x)) + 1.0)")
        self.assertEqual(repr(parse("x^2-1").simplify()), "((x - 1.0) * (x + 1.0))")
        self.assertEqual(repr(parse("(x+1)*(x-1)").simplify()), "((x + 1.0) * (x - 1.0))")
        self.assertEqual(repr(parse("x/x").simplify()), "1.0")
        self.assertEqual(repr(parse("x-x").simplify()), "0.0")
        self.assertEqual(repr(parse("(x^2-1)/(x-1)").simplify()), "(x + 1.0)")
        self.assertEqual(repr(parse("(2*x)/2").simplify()), "x")
        self.assertEqual(repr(parse("x+x").simplify()), "(2.0 * x)")
        self.assertEqual(repr(parse("2*(x/2)").simplify()), "x")

    def test_differentiation(self):
        tests = {
            "x^2": 2*1,
            "sin(x)": 0.54030230586,
            "cos(x)": -0.8414709848,
            "ln(x)": 1.0,
            "exp(x)": 2.71828182846,
            "x*sin(x)": 1.38177329068
        }
        for expr, val in tests.items():
            self.assertAlmostEqual(numerical_derivative(parse(expr), 'x', 1), val, places=5)

    def test_integration(self):
        self.assertEqual(repr(parse("x").integrate('x')), "((x ^ 2.0) / 2.0)")
        self.assertEqual(repr(parse("2*x").integrate('x')), "(x ^ 2.0)")
        self.assertEqual(repr(parse("sin(x)").integrate('x')), "(-1.0 * cos(x))")
        self.assertEqual(repr(parse("cos(x)").integrate('x')), "sin(x)")
        self.assertEqual(repr(parse("exp(x)").integrate('x')), "exp(x)")
        self.assertEqual(repr(parse("(2*x+1)^2").integrate('x')), "((((2.0 * x) + 1.0) ^ 3.0) / 6.0)")

        # Verify by differentiating back
        self.assertEqual(repr(parse("x").integrate('x').differentiate('x').simplify()), "x")
        self.assertEqual(repr(parse("cos(x)").integrate('x').differentiate('x').simplify()), "cos(x)")

if __name__ == '__main__':
    unittest.main()
