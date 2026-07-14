# SentinelAI — Filesystem Security

The FilesystemTool introduces a comprehensive security boundary designed around Zero Trust principles. While the actual file I/O operations are pending implementation, the security validation layer (`PathValidator`) is complete and actively tested.

## The Zero Trust Boundary

The FilesystemTool does not trust the `Plan.parameters["path"]`. This path could originate from a user's regex match, or eventually from a hallucinating LLM.

Before any OS operation occurs, the path string must pass through the `PathValidator` (`app/tools/filesystem/validator.py`).

## Validation Pipeline

The `PathValidator` enforces the following rules in order:

1. **Non-empty:** The path must not be empty or purely whitespace.
2. **Canonicalization:** The path is expanded (`~` to user home) and resolved to its canonical absolute form using `Path.resolve(strict=False)`. This resolves symlinks and eliminates directory traversal attempts (e.g., `../`).
3. **Allowed Roots:** The canonical path must fall under an explicitly configured `AllowedRoot`.
4. **Blocked Patterns:** The relative path (the portion within the root) must not contain any blocked directory names (e.g., `Windows`, `AppData`).
5. **Permissions:** The matching `AllowedRoot` must explicitly permit the requested operation (`FileOperation.READ`, `WRITE`, or `DELETE`).

If validation passes, it returns a frozen `ValidatedPath` object. If any check fails, it raises a `PathValidationError` with a descriptive reason, and the operation is aborted.

## Configuration (`app/tools/filesystem/config.py`)

### Allowed Roots

Only paths under explicitly configured roots are accessible. 

```python
@dataclass(frozen=True, slots=True)
class AllowedRoot:
    path: Path
    readable: bool = True
    writable: bool = False
    deletable: bool = False
```

Default roots are scoped to the current user:
- `~/Documents` (Read, Write)
- `~/Desktop` (Read, Write)
- `~/Downloads` (Read only)

**Security Note:** Delete permissions are disabled (`False`) on all roots by default.

### Blocked Patterns

Even within an allowed root, certain directory names are strictly off-limits to prevent accessing local caches, recycle bins, or misconfigured root-level installations.

```python
BLOCKED_PATTERNS = (
    "windows",
    "program files",
    "program files (x86)",
    "$recycle.bin",
    "system volume information",
    "appdata",
)
```
*Note: The validator checks these case-insensitively.*

### Size Limits

To prevent denial-of-service, max file sizes are defined for future read/write operations:
- `MAX_READ_SIZE_BYTES = 10 MB`
- `MAX_WRITE_SIZE_BYTES = 10 MB`

## Why This Architecture?

- **Defense in Depth:** The allowed roots provide the primary boundary. The blocked patterns provide a secondary boundary against misconfiguration. Canonicalization prevents traversal.
- **Independence:** The `PathValidator` is completely independent of the `PolicyEngine`. The PolicyEngine approves the *intent* (e.g., `read_file` = MEDIUM risk), while the `PathValidator` approves the *target*.
- **Testability:** The validator performs zero file I/O during validation (`strict=False`), making it purely logical and highly testable (38 dedicated tests).
