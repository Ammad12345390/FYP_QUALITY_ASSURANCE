"""
This module provides the AST Tree Analyzer main module.
It generates a visual Abstract Syntax Tree (AST) for given Python code.
"""

import ast
import sys

# Tree symbols for visual output
PIPE = "│"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "


class ASTTree:
    """
    ASTTree generates a readable, visual tree structure of a Python Abstract Syntax Tree (AST).
    """

    def __init__(self, code, output_file=sys.stdout):
        self._output_file = output_file
        self._generator = _ASTGenerator(code)

    def generate(self):
        """Generate and print the AST tree."""
        tree_lines = self._generator.build_tree()

        # ✅ Write output safely
        if isinstance(self._output_file, str):
            with open(self._output_file, mode="w", encoding="UTF-8") as f:
                for line in tree_lines:
                    print(line, file=f)
        else:
            for line in tree_lines:
                print(line, file=self._output_file)


class _ASTGenerator:
    """
    Helper class that builds and formats the AST tree structure.
    """

    def __init__(self, code):
        self._code = code
        self._tree = []
        try:
            # Parse the source code into an AST
            self._ast_root = ast.parse(code)
        except SyntaxError as e:
            print(f"❌ Syntax Error while parsing code: {e}")
            self._ast_root = None

    def build_tree(self):
        """Build and return the formatted AST tree."""
        if not self._ast_root:
            return ["No valid AST generated."]
        self._tree_head()
        self._tree_body(self._ast_root)
        return self._tree

    def _tree_head(self):
        """Add header for the AST tree."""
        self._tree.append("📘 Abstract Syntax Tree (AST)")
        self._tree.append(PIPE)

    def _tree_body(self, node, prefix=""):
        """
        Recursively build the AST structure in visual tree format.
        Each AST node type is printed with indentation and connectors.
        """
        if not isinstance(node, ast.AST):
            return

        fields = [(name, getattr(node, name)) for name in node._fields or []]
        entries_count = len(fields)

        for index, (name, value) in enumerate(fields):
            connector = ELBOW if index == entries_count - 1 else TEE
            line = f"{prefix}{connector} {name}: {self._format_value(value)}"
            self._tree.append(line)

            new_prefix = prefix + (PIPE_PREFIX if index != entries_count - 1 else SPACE_PREFIX)

            if isinstance(value, list):
                for i, item in enumerate(value):
                    sub_connector = ELBOW if i == len(value) - 1 else TEE
                    self._tree.append(f"{new_prefix}{sub_connector} [list item]: {self._node_name(item)}")
                    sub_prefix = new_prefix + (PIPE_PREFIX if i != len(value) - 1 else SPACE_PREFIX)
                    self._tree_body(item, sub_prefix)
            elif isinstance(value, ast.AST):
                self._tree_body(value, new_prefix)

    def _format_value(self, value):
        """Format node field values (AST nodes, lists, constants)."""
        if isinstance(value, ast.AST):
            return self._node_name(value)
        elif isinstance(value, list):
            return f"List[{len(value)}]"
        else:
            return repr(value)

    def _node_name(self, node):
        """Return a readable name for an AST node."""
        if isinstance(node, ast.AST):
            return node.__class__.__name__
        return repr(node)


def main():
    """Main entry point for the AST Tree Analyzer."""
    example_code = """
def greet(name):
    message = f"Hello, {name}!"
    print(message)
"""
    tree = ASTTree(example_code)
    tree.generate()


if __name__ == "__main__":
    main()