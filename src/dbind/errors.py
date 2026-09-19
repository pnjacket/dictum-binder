"""ERR-* exception classes — the error catalog of Interfaces & Contracts.

A leaf module every component may import. Each class carries its stable
code, its exit code (PATTERN-EXIT-CODES) and a ``details`` mapping shaped
per OUT-ERROR. Findings inside ``details`` are Model ``Finding`` objects;
the Renderer projects them.
"""

from __future__ import annotations

from typing import Any


class DbindError(Exception):
    """Base of every contracted failure. DICT: PATTERN-ERROR-ENVELOPE"""

    code: str = "ERR-INTERNAL"
    exit_code: int = 2

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details if details is not None else {}


class UsageError(DbindError):
    """DICT: ERR-USAGE"""

    code = "ERR-USAGE"
    exit_code = 1

    def __init__(self, message: str, usage: str, command: str = "") -> None:
        super().__init__(message, {"usage": usage})
        self.command = command


class FileMissingError(DbindError):
    """DICT: ERR-FILE-MISSING"""

    code = "ERR-FILE-MISSING"
    exit_code = 2

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            f"target file not found: {path} — run `dbind init` first",
            {"path": path, "reason": reason},
        )


class FileExistsAlreadyError(DbindError):
    """DICT: ERR-FILE-EXISTS"""

    code = "ERR-FILE-EXISTS"
    exit_code = 1

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"target already exists: {path}", {"path": path, "reason": reason})


class FileIOError(DbindError):
    """DICT: ERR-IO"""

    code = "ERR-IO"
    exit_code = 2

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            f"cannot access target: {path}: {reason}", {"path": path, "reason": reason}
        )


class ParseError(DbindError):
    """DICT: ERR-PARSE"""

    code = "ERR-PARSE"
    exit_code = 2

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            f"target is not a loadable map: {path}: {reason}", {"path": path, "reason": reason}
        )


class FileTooLargeError(DbindError):
    """DICT: ERR-FILE-TOO-LARGE"""

    code = "ERR-FILE-TOO-LARGE"
    exit_code = 1

    def __init__(self, path: str, size: int, cap: int) -> None:
        super().__init__(
            f"target is {size} bytes, above the {cap}-byte cap; pass --no-size-limit to lift it",
            {"path": path, "reason": f"size {size} > cap {cap}"},
        )


class SchemaVersionError(DbindError):
    """DICT: ERR-SCHEMA-VERSION"""

    code = "ERR-SCHEMA-VERSION"
    exit_code = 1

    def __init__(self, found: int | None, expected: int) -> None:
        super().__init__(
            f"schema_version {found!r} does not match this dictum-binder build's schema version "
            f"{expected}",
            {"found": found, "expected": expected},
        )


class FileInvalidError(DbindError):
    """DICT: ERR-FILE-INVALID"""

    code = "ERR-FILE-INVALID"
    exit_code = 1

    def __init__(self, findings: list[Any]) -> None:
        super().__init__(
            f"the map has {len(findings)} error-level finding(s); fix them by hand, then retry",
            {"findings": findings},
        )


class NotFoundError(DbindError):
    """DICT: ERR-NOT-FOUND"""

    code = "ERR-NOT-FOUND"
    exit_code = 1

    def __init__(self, message: str, id: str | None, anchor: Any | None) -> None:
        super().__init__(message, {"id": id, "anchor": anchor})


class DuplicateError(DbindError):
    """DICT: ERR-DUPLICATE"""

    code = "ERR-DUPLICATE"
    exit_code = 1

    def __init__(self, message: str, id: str | None, anchor: Any) -> None:
        super().__init__(message, {"id": id, "anchor": anchor})


class InputInvalidError(DbindError):
    """DICT: ERR-INPUT-INVALID"""

    code = "ERR-INPUT-INVALID"
    exit_code = 1

    def __init__(self, findings: list[Any]) -> None:
        super().__init__(
            f"input rejected with {len(findings)} finding(s); nothing written",
            {"findings": findings},
        )


class InternalError(DbindError):
    """DICT: ERR-INTERNAL"""

    code = "ERR-INTERNAL"
    exit_code = 2

    def __init__(self, message: str, exception: str) -> None:
        super().__init__(message, {"exception": exception})
