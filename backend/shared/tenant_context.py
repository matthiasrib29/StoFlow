"""
Tenant context using ContextVar for async-safe tenant identification.

Provides a way to access the current tenant (user) ID from anywhere
in the call stack without passing it explicitly through every function.

Uses Python's contextvars module, which is async-safe (each asyncio Task
gets its own copy of the context).

Issue #16 - Business Logic Audit.
"""
from contextvars import ContextVar

_current_tenant_id: ContextVar[int | None] = ContextVar(
    "current_tenant_id", default=None
)


def set_current_tenant_id(user_id: int) -> None:
    """
    Set the current tenant ID for this context (request/task).

    Called during request dependency injection (get_user_db).

    Args:
        user_id: The authenticated user's ID.
    """
    _current_tenant_id.set(user_id)


def get_current_tenant_id() -> int | None:
    """
    Get the current tenant ID, or None if not set.

    Returns:
        The current tenant user ID, or None.
    """
    return _current_tenant_id.get()


def require_current_tenant_id() -> int:
    """
    Get the current tenant ID, raising if not set.

    Use this in code paths that must always run within a tenant context.

    Returns:
        The current tenant user ID.

    Raises:
        RuntimeError: If no tenant context is set.
    """
    tenant_id = _current_tenant_id.get()
    if tenant_id is None:
        raise RuntimeError(
            "No tenant context set. This code must run within a request "
            "or task that has called set_current_tenant_id()."
        )
    return tenant_id
