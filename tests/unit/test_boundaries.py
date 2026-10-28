"""campus_common boundary guard: stdlib + bcrypt only, no siblings, flask stays lazy.

campus.common is the stable kernel of the campus namespace: every other
campus.* distribution depends on it, never the reverse, and its only
third-party runtime dependency is bcrypt. flask/werkzeug may appear ONLY
as function-level lazy imports (errors/handlers.py runs inside a live
Flask app's error path; hoisting them to module level reinstates the
campus.common -> flask edge, #861).

Checked with ast over the source files rather than by importing, so the
guard cannot itself be defeated by import-time side effects.
"""

import ast
import pathlib
import unittest

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "campus" / "common"
LAZY_ONLY = {"flask", "werkzeug"}


def iter_module_trees():
    for path in sorted(SRC.rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"))


def import_targets(node: ast.stmt):
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name
    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        yield node.module


class TestCommonBoundaries(unittest.TestCase):
    """AST checks over src/campus/common (see module docstring)."""

    def test_no_campus_sibling_imports(self):
        offenders = []
        for path, tree in iter_module_trees():
            for node in ast.walk(tree):
                for target in import_targets(node):
                    if target == "campus":
                        offenders.append(f"{path.relative_to(SRC)}: import campus")
                    elif target.startswith("campus.") and target[len("campus."):].split(".", 1)[0] != "common":
                        offenders.append(f"{path.relative_to(SRC)}: {target}")
        self.assertEqual(
            [],
            offenders,
            "campus.common must not import sibling campus.* packages",
        )

    def test_flask_werkzeug_only_as_function_level_imports(self):
        offenders = []
        for path, tree in iter_module_trees():
            for node in tree.body:  # module level only; function bodies are fine
                for target in import_targets(node):
                    if target.split(".", 1)[0] in LAZY_ONLY:
                        offenders.append(f"{path.relative_to(SRC)}: module-level {target}")
        self.assertEqual(
            [],
            offenders,
            "flask/werkzeug must only be imported lazily inside functions (#861)",
        )


if __name__ == "__main__":
    unittest.main()
