from __future__ import annotations

from pathlib import Path

import pytest

from backend_app.adapters.frontend_filesystem import FrontendFilesystemAdapter
from backend_app.application.use_cases.get_index_page import GetIndexPageUseCase
from backend_app.domain.errors import NotFoundError


def test_frontend_filesystem_adapter_paths(tmp_path: Path) -> None:
    adapter = FrontendFilesystemAdapter(frontend_dir=tmp_path)
    assert adapter.index_path() == tmp_path / "pages" / "index.html"
    assert adapter.assets_dir() == tmp_path / "assets"


def test_get_index_page_use_case_success(tmp_path: Path) -> None:
    index = tmp_path / "pages" / "index.html"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text("<html></html>", encoding="utf-8")

    adapter = FrontendFilesystemAdapter(frontend_dir=tmp_path)
    use_case = GetIndexPageUseCase(frontend=adapter)
    assert use_case.execute() == index


def test_get_index_page_use_case_not_found(tmp_path: Path) -> None:
    adapter = FrontendFilesystemAdapter(frontend_dir=tmp_path)
    use_case = GetIndexPageUseCase(frontend=adapter)
    with pytest.raises(NotFoundError, match="Frontend page not found"):
        use_case.execute()

