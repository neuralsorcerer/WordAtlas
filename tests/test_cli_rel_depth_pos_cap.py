from pathlib import Path
from typing import Optional

from typer.testing import CliRunner

from wordatlas.cli import app

runner = CliRunner()


def _fake_render(tmp_path: Path):
    # Lazily import in the closure if needed; avoid unused import at function top
    def fake(self, filename: Optional[str] = None, cleanup: bool = True):
        out = Path(filename or (tmp_path / "graph")).with_suffix(".png")
        out.write_bytes(b"")
        return str(out)

    return fake


def test_cli_rel_depth_and_pos_cap(monkeypatch, tmp_path: Path):
    from graphviz import Digraph

    monkeypatch.setattr(Digraph, "render", _fake_render(tmp_path))

    img = tmp_path / "g.png"
    result = runner.invoke(
        app,
        [
            "graph",
            "run",
            "--depth",
            "2",
            "--rel-depth",
            "synonym:0",
            "--rel-depth",
            "hypernym:1",
            "--pos-cap",
            "a:3",
            "--pos-cap",
            "n:30",
            "--out",
            str(img),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert img.exists()
