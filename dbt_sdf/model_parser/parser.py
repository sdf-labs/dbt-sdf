import re

# Token definitions for inside Jinja2 blocks
TOKEN_SPECIFICATION = [
    # Jinja comments {# ... #} and {#- ... -#}
    ('COMMENT', r'\{#-?[^#]*?-?#\}'),
    ('STM_OPEN', r'\{%-?'),                    # {%- or {%
    ('STM_CLOSE', r'-?%\}'),                   # -%} or %}
    ('EXPR_OPEN', r'\{\{-?'),                  # {{- or {{
    ('EXPR_CLOSE', r'-?\}\}'),                 # -}} or }}
    ('IDENTIFIER', r'[a-zA-Z_]\w*'),           # Identifiers
    ('NUMBER', r'\d+(\.\d*)?'),                # Integer or decimal number
    ('STRING', r'\'[^\']*\'|\"[^\"]*\"'),      # String literals
    ('OP', r'[+\-*/%]'),                       # Arithmetic operators
    ('COMPARE', r'[<>]=?|==|!='),              # Comparison operators
    ('ASSIGN', r'='),                          # Assignment operator
    # Punctuation, including braces, brackets, commas, and colons
    ('PUNCT', r'[{},\[\].:\(\)]'),
    ('SKIP', r'[ \t]+'),                       # Skip spaces and tabs
    ('NEWLINE', r'\n'),                        # Line endings
]

# Create regex patterns for token recognition inside Jinja2 blocks
TOKEN_REGEX = '|'.join(
    f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION)
TOKEN_RE = re.compile(TOKEN_REGEX)


class Token:
    EMPTY = None  # Placeholder for the empty token, defined below

    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({repr(self.type)}, {repr(self.value)}, {self.line}, {self.column})"


Token.EMPTY = Token('EMPTY', '', 0, 0)


def tokenize_jinja_block(code, line_number, line_start):
    """Tokenize content inside Jinja2 blocks, handling nested structures."""
    tokens = []
    pos = 0
    brace_stack = []

    while pos < len(code):
        match = TOKEN_RE.match(code[pos:])
        if match:
            kind = match.lastgroup
            value = match.group(kind)
            column = line_start + pos + 1  # Adjusted to 1-based index for column

            # Handle brace nesting
            if value == '{':
                brace_stack.append('{')
            elif value == '}':
                if brace_stack:
                    brace_stack.pop()

            # Append token to the list
            tokens.append(Token(kind, value, line_number, column))
            pos += len(value)

            # If EXPR_CLOSE or STM_CLOSE is found and stack is empty, break
            if (kind == 'EXPR_CLOSE' or kind == 'STM_CLOSE') and not brace_stack:
                break
        else:
            break

    return tokens, pos


def tokenize(code):
    """Tokenize the input string."""
    line_number = 1
    line_start = 0
    tokens = []
    pos = 0

    while pos < len(code):
        # Look for the next Jinja2 block start
        jinja_start = re.search(r'(\{\{|\{%|\{#)', code[pos:])
        if jinja_start:
            start_pos = jinja_start.start() + pos
            if start_pos > pos:
                # Capture the text before the Jinja2 block as a TEXT token
                text_value = code[pos:start_pos]
                tokens.append(Token('TEXT', text_value,
                              line_number, pos - line_start + 1))
                pos = start_pos
                line_start = pos  # Update line_start after TEXT token

            # Now tokenize the Jinja2 block
            jinja_type = jinja_start.group(0)
            if jinja_type in ('{{', '{%'):
                block_tokens, consumed = tokenize_jinja_block(
                    code[start_pos:], line_number, line_start)
                tokens.extend(block_tokens)
                pos = start_pos + consumed
            else:  # For comments {#
                end_pos = code.find('#}', start_pos) + 2
                tokens.append(Token(
                    'COMMENT', code[start_pos:end_pos], line_number, start_pos - line_start + 1))
                pos = end_pos
        else:
            # No more Jinja2 blocks, capture the rest as TEXT
            tokens.append(
                Token('TEXT', code[pos:], line_number, pos - line_start + 1))
            break

    return [tok for tok in tokens if tok.type != 'SKIP']

# Example usage


def test_scanner0():
    code = "Hello, {{ user.name }} is logged in. {% if user.is_admin %}Admin{% endif %}"
    tokens = tokenize(code)
    for token in tokens:
        print(token)
# test_scanner0()


def test_scanner():
    code = "{{ result = 42 }}bla {  { {% if x > 10 %}haha_)*&^ {% endif %}"
    print(code)
    tokens = tokenize(code)
    for token in tokens:
        print(token)


def test_scanner2():
    code = "{% for item in list %}Item: {{ item }}{% endfor %}"
    print(code)
    tokens = tokenize(code)
    for token in tokens:
        print(token)
# test_scanner2()

# def test_whitespace_control():
#         code = "{%- if x > 10 -%}\n \
#                {{- result = 42 -}}{% endif -%}"
#         print(code)
#         tokens = tokenize(code)
#         for token in tokens:
#             print(token)

# test_whitespace_control()


class Node:
    def __init__(self, token, children=None):
        self.token = token
        self.children = children or []

    def __repr__(self):
        return self.pretty_repr()

    def pretty_repr(self, indent=0):
        """Recursively generate a pretty representation of the node."""
        ind = '    ' * indent  # 4 spaces per indent level
        token_repr = repr(self.token)
        if self.children:
            children_repr = ',\n'.join(self._child_repr(
                child, indent + 2) for child in self.children)
            return f"{ind}{self.__class__.__name__}(\n{ind}    {token_repr},\n{ind}    [\n{children_repr}\n{ind}    ]\n{ind})"
        else:
            return f"{ind}{self.__class__.__name__}({token_repr}, [])"

    def _child_repr(self, child, indent):
        """Helper method to represent a child."""
        ind = '    ' * indent
        if isinstance(child, Node):
            return child.pretty_repr(indent)
        elif isinstance(child, list):
            if not child:
                return f"{ind}[]"
            list_repr = ',\n'.join(self._child_repr(
                c, indent + 1) for c in child)
            return f"{ind}[\n{list_repr}\n{ind}]"
        else:
            return ind + repr(child)


class Statement(Node):
    pass


class Expression(Node):
    pass


# class IfStatement(Statement):
#     pass
class ConditionBlock(Node):
    def __init__(self, open_token, condition, close_token, block):
        super().__init__(Token.EMPTY)
        self.open_token = open_token
        self.condition = condition
        self.close_token = close_token
        self.block = block

    def __repr__(self):
        # print(self)
        return (f"ConditionBlock(\n"
                f"    {repr(self.open_token)},\n"
                f"    {repr(self.condition)},\n"
                f"    {repr(self.close_token)},\n"
                f"    {repr(self.block)}\n"
                f")")


class IfStatement(Node):
    def __init__(self, clauses, endif_token, close_token):
        super().__init__(Token.EMPTY)
        self.clauses = clauses  # List of ConditionBlock or simple else clause
        self.endif_token = endif_token
        self.close_token = close_token

    def __repr__(self):
        clauses_repr = ',\n'.join(repr(clause) for clause in self.clauses)
        return (f"IfStatement(\n"
                f"    [\n{clauses_repr}\n    ],\n"
                f"    {repr(self.endif_token)},\n"
                f"    {repr(self.close_token)}\n"
                f")")


class ForStatement(Statement):
    pass


class SetStatement(Statement):
    pass


class MacroDefinition(Statement):
    pass


class ReturnStatement(Statement):
    pass


class DoStatement(Statement):
    pass


class WithStatement(Statement):
    pass


class FunctionCall(Expression):
    pass


class Literal(Expression):
    pass


class Variable(Expression):
    pass


class BinaryOp(Expression):
    pass


class UnaryOp(Expression):
    pass


class AttributeAccess(Node):
    pass


class IndexAccess(Node):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.index = 0
        self.next_token()

    def next_token(self):
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
            self.index += 1
        else:
            self.current_token = None

    def expect(self, token_type):
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.next_token()
            return token
        raise SyntaxError(f"Expected token {token_type}, got {self.current_token}")

    def parse(self):
        return self.parse_template()

    def parse_template(self, end_tokens=None):
        if end_tokens is None:
            end_tokens = []  # Treat None as an empty list
        elements = []
        while self.current_token:
            if self.current_token.type == 'STM_OPEN':
                # Check if there are more tokens to peek at
                if self.index < len(self.tokens):
                    next_token = self.tokens[self.index]
                    if next_token.type == 'IDENTIFIER' and next_token.value in end_tokens:
                        break
                elements.append(self.parse_statement())
            elif self.current_token.type == 'EXPR_OPEN':
                elements.append(self.parse_statement())
            elif self.current_token.type == 'COMMENT':
                elements.append(self.parse_comment())
            elif self.current_token.type == 'TEXT':
                text_node = self.parse_text()
                if text_node:
                    elements.append(text_node)
            else:
                break  # Should not happen, but ensures safety
        return elements

    def next_token(self):
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
            self.index += 1
        else:
            self.current_token = None

    def parse_text(self):
        """Parses contiguous text as a single TEXT node."""
        text_content = []
        if self.current_token and self.current_token.type == 'TEXT':
            start_line = self.current_token.line
            start_column = self.current_token.column
            while self.current_token and self.current_token.type == 'TEXT':
                text_content.append(self.current_token.value)
                self.next_token()
            if text_content:
                combined_text = ''.join(text_content)
                return Node(Token('TEXT', combined_text, start_line, start_column))
        return None


    def parse_comment(self):
        """Parses a comment and returns a Node."""
        start_token = self.expect(
            'COMMENT')  # Expect the '{# ... #}' comment token
        return Node(start_token)

    def expect(self, token_type):
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.next_token()
            return token
        raise SyntaxError(f"Expected token {token_type}, got {self.current_token}")

    def next_token(self):
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
            self.index += 1
        else:
            self.current_token = None

    def peek_next_token(self):
        """Peek at the next token without advancing the current position."""
        next_index = self.index + 1
        if next_index < len(self.tokens):
            return self.tokens[next_index]
        return None

    def peek_next_token2(self):
        """Peek at the next token without advancing the current position."""
        # next_index = self.index + 1
        if  self.index < len(self.tokens):
            return self.tokens[self.index]
        return None
    def parse_statement(self):
        if self.current_token.type == 'STM_OPEN':
            open_token = self.current_token
            self.next_token()
            if self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'if':
                return self.parse_if_statement(open_token)
            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'for':
                return self.parse_for_statement(open_token)
            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'set':
                return self.parse_set_statement(open_token)
            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'macro':
                return self.parse_macro_definition(open_token)
            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'return':
                return self.parse_return_statement(open_token)
            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'do':
                return self.parse_do_statement(open_token)
            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'with':
                return self.parse_with_statement(open_token)
            else:
                raise SyntaxError(f"Unexpected statement type {self.current_token}")
        elif self.current_token.type == 'EXPR_OPEN':
            return self.parse_expression_statement()
        else:
            raise SyntaxError(f"Unexpected token {self.current_token}")

    def parse_if_statement(self, open_token):
        clauses = []

        # Parse the main if condition
        if_condition_token = self.expect('IDENTIFIER')  # Expect 'if'
        condition = self.parse_expression()
        if_close_token = self.expect('STM_CLOSE')  # Expect closing '%}'

        # Parse the block after the if condition
        block = self.parse_template(end_tokens=['elif', 'else', 'endif'])
        clauses.append(ConditionBlock(open_token, condition, if_close_token, block))

        # Parse elif and else clauses
        open_token = None
        while self.current_token and self.current_token.type == 'STM_OPEN':
            open_token = self.current_token
            self.next_token()  # Skip '{%'

            if self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'elif':
                condition_token = self.expect('IDENTIFIER')  # Expect 'elif'
                elif_condition = self.parse_expression()
                elif_close_token = self.expect('STM_CLOSE')  # Expect closing '%}'
                elif_block = self.parse_template(end_tokens=['elif', 'else', 'endif'])
                clauses.append(ConditionBlock(open_token, elif_condition, elif_close_token, elif_block))

            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'else':
                condition_token = self.expect('IDENTIFIER')  # Expect 'else'
                else_close_token = self.expect('STM_CLOSE')  # Expect closing '%}'
                else_block = self.parse_template(end_tokens=['endif'])
                clauses.append(ConditionBlock(open_token, None, else_close_token, else_block))

            elif self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'endif':
                # We encountered 'endif', so break out of the loop
                break

            else:
                break

        # Ensure we properly close the if statement
        # endif_open_token = Token.EMPTY # self.expect('STM_OPEN')  # Capture the STM_OPEN token for 'endif'
        endif_token = self.expect('IDENTIFIER')  # Expect 'endif'
        close_token = self.expect('STM_CLOSE')

        return IfStatement(clauses, open_token, close_token)
    def parse_for_statement(self, open_token):
        token = self.expect('IDENTIFIER')
        var = self.expect('IDENTIFIER')
        self.expect('IDENTIFIER')  # "in"
        iterable = self.parse_expression()
        for_close_token = self.expect('STM_CLOSE')
        block = self.parse_template(end_tokens=['endfor'])
        endfor_open_token = self.expect('STM_OPEN')
        self.expect('IDENTIFIER')
        close_token = self.expect('STM_CLOSE')
        return ForStatement(token, [open_token, var, iterable, for_close_token, block, endfor_open_token, close_token])

    def parse_set_statement(self, open_token):
        token = self.expect('IDENTIFIER')
        var = self.expect('IDENTIFIER')
        self.expect('ASSIGN')
        value = self.parse_expression()
        close_token = self.expect('STM_CLOSE')
        return SetStatement(token, [open_token, var, value, close_token])

    def parse_do_statement(self, open_token):
        token = self.expect('IDENTIFIER')
        expr = self.parse_expression()
        close_token = self.expect('STM_CLOSE')
        return DoStatement(token, [open_token, expr, close_token])

    def parse_macro_definition(self, open_token):
        token = self.expect('IDENTIFIER')
        name = self.expect('IDENTIFIER')
        self.expect('PUNCT')  # "("
        parameters = []
        if self.current_token.type != 'PUNCT' or self.current_token.value != ')':
            parameters.append(self.expect('IDENTIFIER'))
            while self.current_token.type == 'PUNCT' and self.current_token.value == ',':
                self.next_token()
                parameters.append(self.expect('IDENTIFIER'))
        self.expect('PUNCT')  # ")"
        macro_end_token = self.expect('STM_CLOSE')
        block = self.parse_template(end_tokens=['endmacro'])
        end_macro_open_token = self.expect('STM_OPEN')
        self.expect('IDENTIFIER')
        close_token = self.expect('STM_CLOSE')
        return MacroDefinition(token, [open_token, name, parameters, macro_end_token, block, end_macro_open_token, close_token])

    def parse_return_statement(self, open_token):
        token = self.expect('IDENTIFIER')
        if self.current_token.type != 'STM_CLOSE':
            value = self.parse_expression()
        else:
            value = None
        close_token = self.expect('STM_CLOSE')
        return ReturnStatement(token, [open_token, value, close_token])

    def parse_with_statement(self, open_token):
        token = self.expect('IDENTIFIER')
        pairs = []
        pairs.append(self.parse_with_pair())
        while self.current_token.type == 'PUNCT' and self.current_token.value == ',':
            self.next_token()
            pairs.append(self.parse_with_pair())
        self.expect('STM_CLOSE')
        block = self.parse_template(end_tokens=['endwith'])
        self.expect('STM_OPEN')
        self.expect('IDENTIFIER')
        close_token = self.expect('STM_CLOSE')
        return WithStatement(token, [open_token, pairs, block, close_token])

    def parse_with_pair(self):
        var = self.expect('IDENTIFIER')
        self.expect('ASSIGN')
        value = self.parse_expression()
        return (var, value)

    def parse_expression_statement(self):
        open_token = self.expect('EXPR_OPEN')
        expr = self.parse_expression()
        close_token = self.expect('EXPR_CLOSE')
        return Expression(Token.EMPTY, [open_token, expr, close_token])

    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        node = self.parse_logical_and()
        while self.current_token and self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'or':
            op_token = self.current_token
            self.next_token()
            right = self.parse_logical_and()
            node = BinaryOp(op_token, [node, right])
        return node

    def parse_logical_and(self):

        node = self.parse_equality()
        while self.current_token and self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'and':
            op_token = self.current_token
            self.next_token()
            right = self.parse_equality()
            node = BinaryOp(op_token, [node, right])
        return node

    def parse_equality(self):
        node = self.parse_comparison()
        while self.current_token and self.current_token.type == 'COMPARE' and self.current_token.value in ('==', '!='):
            op_token = self.current_token
            self.next_token()
            right = self.parse_comparison()
            node = BinaryOp(op_token, [node, right])
        return node

    def parse_comparison(self):
        node = self.parse_arithmetic()
        while self.current_token and self.current_token.type == 'COMPARE' and self.current_token.value in ('>', '<', '>=', '<='):
            op_token = self.current_token
            self.next_token()
            right = self.parse_arithmetic()
            node = BinaryOp(op_token, [node, right])
        return node

    def parse_arithmetic(self):

        node = self.parse_term()
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ('+', '-'):
            op_token = self.current_token
            self.next_token()
            right = self.parse_term()
            node = BinaryOp(op_token, [node, right])
        return node

    def parse_term(self):

        node = self.parse_factor()
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ('*', '/', '%'):
            op_token = self.current_token
            self.next_token()
            right = self.parse_factor()
            node = BinaryOp(op_token, [node, right])
        return node

    def parse_factor(self):
        # Handle unary operators: '-' and 'not'
        if (self.current_token.type == 'OP' and self.current_token.value == '-') or \
                (self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'not'):
            op_token = self.current_token
            self.next_token()
            right = self.parse_factor()  # Recursively parse the next factor
            return UnaryOp(op_token, [right])

        return self.parse_primary()

    def parse_primary(self):
        token = self.current_token
        if token.type == 'NUMBER' or token.type == 'STRING':
            self.next_token()
            return Literal(token)
        elif token.type == 'IDENTIFIER':
            self.next_token()
            node = Variable(token)
            while self.current_token and self.current_token.type == 'PUNCT':
                if self.current_token.value == '.':
                    node = self.parse_attribute_access(node)
                elif self.current_token.value == '[':
                    node = self.parse_index_access(node)
                elif self.current_token.value == '(':
                    node = self.parse_function_call(node)
                else:
                    break
            return node
        elif token.type == 'PUNCT' and token.value == '(':
            self.next_token()
            expr = self.parse_expression()
            self.expect('PUNCT')  # Expecting ')'
            return expr
        elif token.type == 'PUNCT' and token.value == '[':
            return self.parse_list_literal()
        elif token.type == 'PUNCT' and token.value == '{':
            return self.parse_object_literal()
        else:
            raise SyntaxError(
                f"Unexpected token in primary expression: {token}")

    def parse_attribute_access(self, base):
        """Parse object field access."""
        self.expect('PUNCT')  # Expecting '.'
        field = self.expect('IDENTIFIER')
        return AttributeAccess(Token.EMPTY, [base, field])

    def parse_index_access(self, base):
        """Parse array index access."""
        self.expect('PUNCT')  # Expecting '['
        index = self.parse_expression()
        self.expect('PUNCT')  # Expecting ']'
        return IndexAccess(Token.EMPTY, [base, index])

    def parse_function_call(self, base):
        self.expect('PUNCT')  # Expecting '('
        args = []
        if self.current_token.type != 'PUNCT' or self.current_token.value != ')':
            args.append(self.parse_argument())
            while self.current_token.type == 'PUNCT' and self.current_token.value == ',':
                self.next_token()
                args.append(self.parse_argument())
        self.expect('PUNCT')  # Expecting ')'
        # prepend base to args
        args.insert(0, base)
        return FunctionCall(Token.EMPTY,args)


    def parse_argument(self):
        """Parse an argument, which can be either positional or named."""
        if self.current_token.type == 'IDENTIFIER':
            # Peek ahead to see if this is a named argument
            next_token = self.peek_next_token2()
            if next_token and next_token.type == 'ASSIGN':
                name_token = self.current_token
                self.next_token()  # Skip the identifier
                self.next_token()  #Skip the '='
                value = self.parse_expression()
                # named args are tuples of (name, value)
                return (name_token, value) 
        # If it's not a named argument, parse it as an expression
        return self.parse_expression()



    def parse_list_literal(self):
        token = self.expect('PUNCT')  # Expecting '['
        elements = []
        if self.current_token.type != 'PUNCT' or self.current_token.value != ']':
            elements.append(self.parse_expression())
            while self.current_token.type == 'PUNCT' and self.current_token.value == ',':
                self.next_token()
                elements.append(self.parse_expression())
        self.expect('PUNCT')  # Expecting ']'
        return Literal(token, elements)

    def parse_object_literal(self):
        token = self.expect('PUNCT')  # Expecting '{'
        pairs = []
        if self.current_token.type != 'PUNCT' or self.current_token.value != '}':
            pairs.append(self.parse_key_value_pair())
            while self.current_token.type == 'PUNCT' and self.current_token.value == ',':
                self.next_token()
                pairs.append(self.parse_key_value_pair())
        self.expect('PUNCT')  # Expecting '}'
        return Literal(token, pairs)

    def parse_key_value_pair(self):
        # Keys can be either IDENTIFIER or STRING
        if self.current_token.type in ('IDENTIFIER', 'STRING'):
            key = self.current_token
            self.next_token()
        else:
            raise SyntaxError(f"Unexpected token {self.current_token}, expected IDENTIFIER or STRING as key")

        self.expect('PUNCT')  # Expecting ':'
        value = self.parse_expression()
        return (key, value)

    def extract_dbt_calls(code):
        tree = self.parse_code(code)
        config_calls, source_calls, ref_calls = walk_ast(tree)
        return config_calls, source_calls, ref_calls

def test_expression():
    code = "arr[0].b()"
    tokens = tokenize("{{" + code + "}}")
    for token in tokens:
        token.column -= 2
        print(token)
    expression_node = Parser(tokens).parse()[0]  # Get the Expression node
    print(expression_node)


def test_statement():
    code = "{% if x > 10 %}High{% elif x > 5 %}Medium{% else %}Low{% endif %}"
    tokens = tokenize(code)
    for token in tokens:
        print(token)
    parser = Parser(tokens)
    tree = parser.parse()
    print(tree)

test_statement()

def extract_dbt_calls(code):
    """Parse the input string and return lists of config, source, and ref calls.
    Args:
        code: A string containing the Jinja2 template code.
    Returns:
        A tuple of three lists: (config_calls, source_calls, ref_calls)
    """
    # Step 1: Tokenize and parse the code
    tokens = tokenize(code)
    for token in tokens:
        print(token)
    parser = Parser(tokens)
    trees = parser.parse() # Assuming parse() returns a list of nodes

    # Step 2: Walk the AST and collect the desired calls
    config_calls = []
    source_calls = []
    ref_calls = []

    def walk_ast(node):
        if node is None:
            return

        if isinstance(node, FunctionCall):
            func_name = node.children[0].token.value
            if func_name == 'config':
                config_calls.append(node)
            elif func_name == 'source':
                source_calls.append(node)
            elif func_name == 'ref':
                ref_calls.append(node)

        for child in node.children:
            if isinstance(child, Node):
                walk_ast(child)
    for tree in trees:
        walk_ast(tree)

    return config_calls, source_calls, ref_calls

def test_extract_dbt_calls(): 
        code = """
        {{ config(materialization = 'view') }}
        {{ source('my_source', 'my_table') }}
        {{ ref('my_model') }}
        """
        config_calls, source_calls, ref_calls = extract_dbt_calls(code)
        print(config_calls)
        print(source_calls)
        print(ref_calls)

# test_extract_dbt_calls() 