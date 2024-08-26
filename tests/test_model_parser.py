# dbt_model_parser/test_parser.py

import unittest

from dbt_sdf.model_parser.parser import (
    Parser, tokenize, Token,
    IfStatement, ForStatement, SetStatement, MacroDefinition,
    ReturnStatement, DoStatement, WithStatement, Expression,
    Variable, Literal, FunctionCall, Node, BinaryOp,
    UnaryOp, Variable, Literal, FunctionCall, Node, AttributeAccess, IndexAccess, ConditionBlock, extract_dbt_calls
)

import unittest


class TestParser(unittest.TestCase):

    def setUp(self):
        self.parser = None
        self.maxDiff = None

    def parse_code(self, code):
        tokens = tokenize(code)
        # for token in tokens:
        #     print(token)
        self.parser = Parser(tokens)
        return self.parser.parse()[0]

    # Test for 'if' statement
    def test_if_statement(self):
        code = "{% if x > 10 %}Text inside if{% endif %}"
        tree = self.parse_code(code)
        # print(tree)
        expected = IfStatement(
            [
                ConditionBlock(
                    Token('STM_OPEN', '{%', 1, 1),
                    BinaryOp(
                        Token('COMPARE', '>', 1, 9),
                        [
                            Variable(Token('IDENTIFIER', 'x', 1, 7), []),
                            Literal(Token('NUMBER', '10', 1, 11), [])
                        ]
                    ),
                    Token('STM_CLOSE', '%}', 1, 14),
                    [Node(Token('TEXT', 'Text inside if', 1, 16), [])]
                )
            ],
            Token('STM_OPEN', '{%', 1, 30),
            Token('STM_CLOSE', '%}', 1, 39)
        )
        self.assertEqual(repr(tree), repr(expected))

    def test_if_else_endif(self):
        code = "{% if x > 10 %}High{% elif x > 5 %}Medium{% else %}Low{% endif %}"
        tree = self.parse_code(code)
        expect = IfStatement(
            [
                ConditionBlock(
                    Token('STM_OPEN', '{%', 1, 1),
                    BinaryOp(
                        Token('COMPARE', '>', 1, 9),
                        [
                            Variable(Token('IDENTIFIER', 'x', 1, 7), []),
                            Literal(Token('NUMBER', '10', 1, 11), [])
                        ]
                    ),
                    Token('STM_CLOSE', '%}', 1, 14),
                    [Node(Token('TEXT', 'High', 1, 16), [])]
                ),
                ConditionBlock(
                    Token('STM_OPEN', '{%', 1, 20),
                    BinaryOp(
                        Token('COMPARE', '>', 1, 30),
                        [
                            Variable(Token('IDENTIFIER', 'x', 1, 28), []),
                            Literal(Token('NUMBER', '5', 1, 32), [])
                        ]
                    ),
                    Token('STM_CLOSE', '%}', 1, 34),
                    [Node(Token('TEXT', 'Medium', 1, 17), [])]
                ),
                ConditionBlock(
                    Token('STM_OPEN', '{%', 1, 42),
                    None,
                    Token('STM_CLOSE', '%}', 1, 50),
                    [Node(Token('TEXT', 'Low', 1, 11), [])]
                )
            ],
            Token('STM_OPEN', '{%', 1, 55),
            Token('STM_CLOSE', '%}', 1, 64)
        )
        self.assertEqual(repr(tree), repr(expect))

    # Test for 'for' statement

    def test_for_statement(self):
        code = "{% for item in list %}Item: {{ item }}{% endfor %}"
        tree = self.parse_code(code)

        expected = ForStatement(
            Token('IDENTIFIER', 'for', 1, 4),
            [
                Token('STM_OPEN', '{%', 1, 1),
                Token('IDENTIFIER', 'item', 1, 8),
                Variable(Token('IDENTIFIER', 'list', 1, 16), []),
                Token('STM_CLOSE', '%}', 1, 21),
                [
                    Node(Token('TEXT', 'Item: ', 1, 23), []),
                    Expression(
                        Token('EMPTY', '', 0, 0),
                        [
                            Token('EXPR_OPEN', '{{', 1, 29),
                            Variable(Token('IDENTIFIER', 'item', 1, 32), []),
                            Token('EXPR_CLOSE', '}}', 1, 37)
                        ]
                    )
                ],
                Token('STM_OPEN', '{%', 1, 29),
                Token('STM_CLOSE', '%}', 1, 39)
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for 'set' statement
    def test_set_statement(self):
        code = "{% set var = 42 %}"
        tree = self.parse_code(code)

        expected = SetStatement(
            Token('IDENTIFIER', 'set', 1, 4),
            [
                Token('STM_OPEN', '{%', 1, 1),
                Token('IDENTIFIER', 'var', 1, 8),
                Literal(Token('NUMBER', '42', 1, 14)),
                Token('STM_CLOSE', '%}', 1, 17)
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for 'macro' definition
    def test_macro_definition(self):
        code = "{% macro greet(name) %}Hello {{ name }}{% endmacro %}"
        tree = self.parse_code(code)
        expected = MacroDefinition(
            Token('IDENTIFIER', 'macro', 1, 4),
            [
                Token('STM_OPEN', '{%', 1, 1),
                Token('IDENTIFIER', 'greet', 1, 10),
                [
                    Token('IDENTIFIER', 'name', 1, 16)
                ],
                Token('STM_CLOSE', '%}', 1, 22),
                [
                    Node(Token('TEXT', 'Hello ', 1, 30), []),
                    Expression(
                        Token('EMPTY', '', 0, 0),
                        [
                            Token('EXPR_OPEN', '{{', 1, 30),
                            Variable(Token('IDENTIFIER', 'name', 1, 33), []),
                            Token('EXPR_CLOSE', '}}', 1, 38)
                        ]
                    )
                ],
                Token('STM_OPEN', '{%', 1, 30),
                Token('STM_CLOSE', '%}', 1, 42)
            ]
        )

#         self.assertEqual(repr(tree), repr(expected))

    # Test for 'return' statement
    def test_return_statement(self):
        code = "{% return 100 %}"
        tree = self.parse_code(code)
        expected = ReturnStatement(
            Token('IDENTIFIER', 'return', 1, 4),
            [
                Token('STM_OPEN', '{%', 1, 1),
                Literal(Token('NUMBER', '100', 1, 11), []),
                Token('STM_CLOSE', '%}', 1, 15)
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for 'do' statement
    def test_do_statement(self):
        code = "{% do something() %}"
        tree = self.parse_code(code)
        # print(tree)
        expected = DoStatement(
            Token('IDENTIFIER', 'do', 1, 4),
            [
                Token('STM_OPEN', '{%', 1, 1),
                FunctionCall(
                    Token('EMPTY', '', 0, 0),
                    [
                        Variable(Token('IDENTIFIER', 'something', 1, 7), [])
                    ]
                ),
                Token('STM_CLOSE', '%}', 1, 19)
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for 'with' statement
    def test_with_statement(self):
        code = "{% with x=1, y=2 %}x+y={{ x + y }}{% endwith %}"
        tree = self.parse_code(code)

        expected = WithStatement(
            Token('IDENTIFIER', 'with', 1, 4),
            [
                Token('STM_OPEN', '{%', 1, 1),
                [
                    (Token('IDENTIFIER', 'x', 1, 9), Literal(
                        Token('NUMBER', '1', 1, 11), [])),
                    (Token('IDENTIFIER', 'y', 1, 14), Literal(
                        Token('NUMBER', '2', 1, 16), []))
                ],
                [
                    Node(Token('TEXT', 'x+y=', 1, 20), []),
                    Expression(
                        Token('EMPTY', '', 0, 0),
                        [
                            Token('EXPR_OPEN', '{{', 1, 24),
                            BinaryOp(
                                Token('OP', '+', 1, 29),
                                [
                                    Variable(
                                        Token('IDENTIFIER', 'x', 1, 27), []),
                                    Variable(
                                        Token('IDENTIFIER', 'y', 1, 31), [])
                                ]
                            ),
                            Token('EXPR_CLOSE', '}}', 1, 33)
                        ]
                    )
                ],
                Token('STM_CLOSE', '%}', 1, 35)
            ]
        )

        self.assertEqual(repr(tree), repr(expected))

    # Test for 'expression' statement
    def test_expression_statement(self):
        code = "{{ user.name }}"
        tree = self.parse_code(code)
        expected = Expression(
            Token('EMPTY', '', 0, 0),
            [
                Token('EXPR_OPEN', '{{', 1, 1),
                AttributeAccess(
                    Token('EMPTY', '', 0, 0),
                    [
                        Variable(Token('IDENTIFIER', 'user', 1, 4), []),
                        Token('IDENTIFIER', 'name', 1, 9)
                    ]
                ),
                Token('EXPR_CLOSE', '}}', 1, 14)
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    def test_named_arguments(self):
        code = "{{config(materialization = 'view')}}"
        tree = self.parse_code(code)
        expected = Expression(
            Token('EMPTY', '', 0, 0),
            [
                Token('EXPR_OPEN', '{{', 1, 1),
                FunctionCall(
                    Token('EMPTY', '', 0, 0),
                    [
                        Variable(Token('IDENTIFIER', 'config', 1, 3), []),
                        (Token('IDENTIFIER', 'materialization', 1, 10),
                         Literal(Token('STRING', "'view'", 1, 28), []))
                    ]
                ),
                Token('EXPR_CLOSE', '}}', 1, 35)
            ]
        )
        self.assertEqual(repr(tree), repr(expected))


class TestExpressions(unittest.TestCase):

    def setUp(self):
        self.parser = None
        self.maxDiff = None

    def parse_expression(self, code):
        tokens = tokenize("{{" + code + " }}")
        for token in tokens:
            token.column -= 2
        #     print(token)

        self.parser = Parser(tokens)
        expression_node = self.parser.parse()[0]  # Get the Expression node
        # Test for a simple binary operation
        return expression_node.children[1]

    def test_arithmetic_expression(self):
        code = "5 + 3"
        tree = self.parse_expression(code)
        # print (tree)
        expected = BinaryOp(
            Token('OP', '+', 1, 3),
            [
                Literal(Token('NUMBER', '5', 1, 1)),
                Literal(Token('NUMBER', '3', 1, 5))
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for a logical 'and' expression
    def test_logical_and_expression(self):
        code = "a and b or not c"
        tree = self.parse_expression(code)
        expected = BinaryOp(
            Token('IDENTIFIER', 'or', 1, 9),
            [
                BinaryOp(
                    Token('IDENTIFIER', 'and', 1, 3),
                    [
                        Variable(Token('IDENTIFIER', 'a', 1, 1), []),
                        Variable(Token('IDENTIFIER', 'b', 1, 7), [])
                    ]
                ),
                UnaryOp(
                    Token('IDENTIFIER', 'not', 1, 12),
                    [
                        Variable(Token('IDENTIFIER', 'c', 1, 16), [])
                    ]
                )
            ]
        )
        # print("expected" , repr(expected))
        self.assertEqual(repr(tree), repr(expected))

    # Test for a logical 'or' expression
    def test_logical_or_expression(self):
        code = "a or b"
        tree = self.parse_expression(code)
        expected = BinaryOp(
            Token('IDENTIFIER', 'or', 1, 3),
            [
                Variable(Token('IDENTIFIER', 'a', 1, 1)),
                Variable(Token('IDENTIFIER', 'b', 1, 6))
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for an equality comparison
    def test_equality_expression(self):
        code = "a == b"
        tree = self.parse_expression(code)
        expected = BinaryOp(
            Token('COMPARE', '==', 1, 3),
            [
                Variable(Token('IDENTIFIER', 'a', 1, 1), []),
                Variable(Token('IDENTIFIER', 'b', 1, 6), [])
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for a comparison (greater than)
    def test_comparison_expression(self):
        code = "a > 10"
        tree = self.parse_expression(code)
        expected = BinaryOp(
            Token('COMPARE', '>', 1, 3),
            [
                Variable(Token('IDENTIFIER', 'a', 1, 1), []),
                Literal(Token('NUMBER', '10', 1, 5), [])
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for a unary operation (negation)
    def test_unary_operation(self):
        code = " -a"
        tree = self.parse_expression(code)
        expected = UnaryOp(
            Token('OP', '-', 1, 2),
            [
                Variable(Token('IDENTIFIER', 'a', 1, 3), [])
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # # Test for a function call
    # def test_function_call(self):
    #     code = "my_function(42)"
    #     tree = self.parse_expression(code)
    #     print("test_function_call", tree)
    #     expected = FunctionCall(
    #         Token('IDENTIFIER', 'my_function', 1, 1),
    #         [
    #             Literal(Token('NUMBER', '42', 1, 13), [])
    #         ]
    #     )
    #     print("expected", expected)
    #     self.assertEqual(repr(tree), repr(expected))

    # Test for a complex arithmetic expression
    def test_complex_arithmetic_expression(self):
        code = "a * (b + c)"
        tree = self.parse_expression(code)
        expected = BinaryOp(
            Token('OP', '*', 1, 3),
            [
                Variable(Token('IDENTIFIER', 'a', 1, 1), []),
                BinaryOp(
                    Token('OP', '+', 1, 8),
                    [
                        Variable(Token('IDENTIFIER', 'b', 1, 6), []),
                        Variable(Token('IDENTIFIER', 'c', 1, 10), [])
                    ]
                )
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for a list literal
    def test_list_literal(self):
        code = "[1, 2, 3]"
        tree = self.parse_expression(code)
        expected = Literal(
            Token('PUNCT', '[', 1, 1),
            [
                Literal(Token('NUMBER', '1', 1, 2)),
                Literal(Token('NUMBER', '2', 1, 5)),
                Literal(Token('NUMBER', '3', 1, 8))
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for an object literal (dictionary)
    def test_object_literal(self):
        code = " {'key': 1, 'key2': 2}"
        tree = self.parse_expression(code)
        # print(tree)
        expected = Literal(
            Token('PUNCT', '{', 1, 2),
            [
                (Token('STRING', "'key'", 1, 3), Literal(
                    Token('NUMBER', '1', 1, 10), [])),
                (Token('STRING', "'key2'", 1, 13), Literal(
                    Token('NUMBER', '2', 1, 21), []))
            ]
        )
        self.assertEqual(repr(tree), repr(expected))

    # Test for an index/object/function_call access

    def test_index_access(self):
        code = "arr[0].b(12)"
        tree = self.parse_expression(code)
        expected = FunctionCall(
            Token('EMPTY', '', 0, 0),
            [
                AttributeAccess(
                    Token('EMPTY', '', 0, 0),
                    [
                        IndexAccess(
                            Token('EMPTY', '', 0, 0),
                            [
                                Variable(Token('IDENTIFIER', 'arr', 1, 1), []),
                                Literal(Token('NUMBER', '0', 1, 5), [])
                            ]
                        ),
                        Token('IDENTIFIER', 'b', 1, 8)
                    ]
                ),
                Literal(Token('NUMBER', '12', 1, 10), [])
            ]
        )
        self.assertEqual(repr(tree), repr(expected))


class TestDbtCallsExtraction(unittest.TestCase):

    def test_extract_dbt_calls(self):
        code = """
        {{ config(materialization = 'view') }}
        {{ source('my_source', 'my_table') }}
        {{ ref('my_model') }}
        """
        config_calls, source_calls, ref_calls = extract_dbt_calls(code)
        print(config_calls, source_calls, ref_calls)

        # Test that we found one of each call type
        self.assertEqual(len(config_calls), 1)
        self.assertEqual(len(source_calls), 1)
        self.assertEqual(len(ref_calls), 1)

        # Test that the content of the function calls is correct
        self.assertEqual(config_calls[0].children[0].token.value, 'config')
        self.assertEqual(source_calls[0].children[0].token.value, 'source')
        self.assertEqual(ref_calls[0].children[0].token.value, 'ref')

    def test_no_calls(self):
        code = "Just some text with no dbt calls."
        config_calls, source_calls, ref_calls = extract_dbt_calls(code)

        # Test that no calls were found
        self.assertEqual(len(config_calls), 0)
        self.assertEqual(len(source_calls), 0)
        self.assertEqual(len(ref_calls), 0)

    def test_mixed_content(self):
        code = """
        Here is some text {{ config(materialization = 'table') }}
        and here is a ref call {{ ref('another_model') }}
        and a source call {{ source('src', 'tbl') }}.
        """
        config_calls, source_calls, ref_calls = extract_dbt_calls(code)

        # Test that we found one of each call type
        self.assertEqual(len(config_calls), 1)
        self.assertEqual(len(source_calls), 1)
        self.assertEqual(len(ref_calls), 1)


if __name__ == '__main__':
    unittest.main()