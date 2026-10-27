from src.core.boundaries import check_module_boundary_violations


def test_modular_monolith_boundary_linter():
    """Rule BR-1, BR-2: Enforce architectural boundaries.
    No module in src/modules may import models directly from another module.
    Modules communicate exclusively through service interfaces or shared DTOs/schemas.
    """
    violations = check_module_boundary_violations()
    if violations:
        error_msgs = "\n".join([f"{f}:{line}: {msg}" for f, line, msg in violations])
        assert False, f"Rule BR-2 Architectural Boundary Violations found:\n{error_msgs}"
