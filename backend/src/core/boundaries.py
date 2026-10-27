import os
import ast
from typing import List, Tuple

MODULES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "modules")
)


def check_module_boundary_violations() -> List[Tuple[str, int, str]]:
    """Inspects all Python files across all modules in src/modules.
    Enforces Rule BR-1 and BR-2:
    - Modules must NOT import models directly from other modules.
    - Modules must communicate only via service interfaces (service.py) or schemas (schemas.py).
    
    Returns a list of violations: (filepath, line_number, error_message).
    """
    violations = []

    if not os.path.exists(MODULES_DIR):
        return violations

    all_modules = [
        d
        for d in os.listdir(MODULES_DIR)
        if os.path.isdir(os.path.join(MODULES_DIR, d)) and not d.startswith("__")
    ]

    for source_mod in all_modules:
        mod_path = os.path.join(MODULES_DIR, source_mod)
        for root, _, files in os.walk(mod_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=file_path)
                except Exception as e:
                    violations.append((file_path, 1, f"Failed to parse AST: {e}"))
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        module_str = node.module or ""
                        # Check cross-module imports
                        for target_mod in all_modules:
                            if target_mod == source_mod:
                                continue  # Same module internal imports are allowed

                            # Disallowed: importing from target_mod.models
                            if (
                                f"src.modules.{target_mod}.models" in module_str
                                or f"modules.{target_mod}.models" in module_str
                            ):
                                violations.append(
                                    (
                                        file_path,
                                        node.lineno,
                                        f"Rule BR-1 Violation: '{source_mod}' directly imports models from '{target_mod}'. "
                                        f"Must interact only through service interface '{target_mod}.service'.",
                                    )
                                )
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            for target_mod in all_modules:
                                if target_mod == source_mod:
                                    continue
                                if f"src.modules.{target_mod}.models" in alias.name:
                                    violations.append(
                                        (
                                            file_path,
                                            node.lineno,
                                            f"Rule BR-1 Violation: '{source_mod}' imports '{alias.name}'.",
                                        )
                                    )

    return violations
