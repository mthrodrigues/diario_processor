from pathlib import Path


_SHARED_PACKAGE = Path(__file__).resolve().parents[2] / "institutional_contracts"
__path__ = [str(_SHARED_PACKAGE)]

exec(
    (_SHARED_PACKAGE / "__init__.py").read_text(encoding="utf-8"),
    globals(),
)
