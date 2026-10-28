"""campus_common public-interface closed-world guard and manifest check.

The public interface of campus.common is two-tier:

- The module tree is public by definition: importing submodules
  (``from campus.common.utils import url``) is a supported pattern.
- Symbol re-exports are public if and only if they are listed in the
  containing package's ``__all__``. Anything underscore-prefixed is
  private by convention.

These tests keep ``__all__`` honest in both directions (declared names
must actually import; submodules and re-exported symbols must be
declared), and verify the checked-in interface manifest matches
reality, so any interface change is a deliberate, diffable commit that
ships with a CHANGELOG entry and the version bump the diff dictates
(additive -> patch, breaking -> minor).
"""

import ast
import importlib
import json
import pathlib
import unittest

import campus.common

SRC = pathlib.Path(campus.common.__file__).resolve().parent
MANIFEST = pathlib.Path(__file__).resolve().parents[1] / "interface_manifest.json"

# Packages whose __init__ __all__ is contract ("" = campus.common itself).
PACKAGES = ["", "errors", "schema", "utils", "validation"]

# Leaf modules that declare an __all__ of their own.
DECLARED_LEAVES = [
    "env",
    "errors.base",
    "errors.auth_errors",
    "errors.token_errors",
    "errors.validation",
]


def _submodules(package_dir: pathlib.Path) -> set[str]:
    """Non-underscore importable submodule names of a package directory."""
    names = set()
    for child in package_dir.iterdir():
        if child.name.startswith("_"):
            continue
        if child.is_dir() and (child / "__init__.py").exists():
            names.add(child.name)
        elif child.is_file() and child.suffix == ".py":
            names.add(child.name.removesuffix(".py"))
    return names


def _all_of(tree: ast.Module) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if getattr(target, "id", None) == "__all__":
                    return [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
    raise AssertionError("no __all__ defined")


def _package_init(pkg_path: pathlib.Path) -> ast.Module:
    return ast.parse((pkg_path / "__init__.py").read_text(encoding="utf-8"))


def build_interface_manifest() -> dict[str, list[str]]:
    """The full declared-interface snapshot, as a JSON-ready dict."""
    manifest: dict[str, list[str]] = {}
    for pkg in PACKAGES:
        rel = "campus.common" + (f".{pkg}" if pkg else "")
        manifest[rel] = sorted(_all_of(_package_init(SRC / pkg if pkg else SRC)))
    for leaf in DECLARED_LEAVES:
        mod = importlib.import_module(f"campus.common.{leaf}")
        manifest[f"campus.common.{leaf}"] = sorted(mod.__all__)
    return manifest


class TestPackageInterface(unittest.TestCase):
    """__all__ closure rules for every package."""

    def test_all_importable_and_no_underscores(self):
        for pkg in PACKAGES:
            with self.subTest(pkg=pkg or "campus.common"):
                module = importlib.import_module("campus.common" + (f".{pkg}" if pkg else ""))
                for name in module.__all__:
                    self.assertFalse(name.startswith("_"), name)
                    self.assertIsNotNone(getattr(module, name))

    def test_submodules_declared(self):
        """Tree closure: every non-underscore submodule must appear in __all__."""
        for pkg in PACKAGES:
            with self.subTest(pkg=pkg or "campus.common"):
                pkg_dir = SRC / pkg if pkg else SRC
                module = importlib.import_module("campus.common" + (f".{pkg}" if pkg else ""))
                missing = _submodules(pkg_dir) - set(module.__all__)
                self.assertEqual(set(), missing, "submodules missing from __all__")

    def test_init_reexports_declared(self):
        """Every `from .x import Y` in a package __init__ must be declared."""
        for pkg in PACKAGES:
            with self.subTest(pkg=pkg or "campus.common"):
                pkg_dir = SRC / pkg if pkg else SRC
                tree = _package_init(pkg_dir)
                declared = set(_all_of(tree))
                for node in tree.body:
                    if isinstance(node, ast.ImportFrom) and node.level == 1:
                        for alias in node.names:
                            if alias.name != "*" and not alias.name.startswith("_"):
                                self.assertIn(alias.asname or alias.name, declared)


class TestEnvSurface(unittest.TestCase):
    """env.py is the universally-consumed module; its defs must stay declared."""

    def test_public_defs_declared(self):
        tree = ast.parse((SRC / "env.py").read_text(encoding="utf-8"))
        declared = set(_all_of(tree))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names = {node.name}
            elif isinstance(node, ast.Assign):
                names = {t.id for t in node.targets if isinstance(t, ast.Name)}
            else:
                continue  # imports and AnnAssign declarations (ENV) are not defs
            for name in names:
                if not name.startswith("_"):
                    self.assertIn(name, declared, f"env.py defines {name} but does not declare it")


class TestInterfaceManifest(unittest.TestCase):
    """The checked-in manifest must match reality exactly (diff = deliberate)."""

    def test_manifest_matches_reality(self):
        committed = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(committed, build_interface_manifest())


if __name__ == "__main__":
    unittest.main()
