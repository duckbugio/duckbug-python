import sys
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class IntegrationImportsTest(TestCase):
    def test_imports_do_not_require_frameworks(self) -> None:
        # These modules must be importable even if Flask/Django aren't installed,
        # because they only import frameworks lazily.
        import duckbug.integrations.asgi  # noqa: F401
        import duckbug.integrations.flask  # noqa: F401
        import duckbug.integrations.django  # noqa: F401
