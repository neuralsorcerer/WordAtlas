import json
from pathlib import Path
from typing import Optional

from typer.testing import CliRunner

from wordatlas.cli import app

runner = CliRunner()


def test_cli_list_json(tmp_path: Path):
    out = tmp_path / "g.json"
    result = runner.invoke(app, ["list", "happiness", "--depth", "1", "--json-out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["center"] == "happiness"
    assert isinstance(data["nodes"], list)


def test_cli_show_runs():
    result = runner.invoke(app, ["show", "happiness", "--depth", "1"])
    assert result.exit_code == 0
    assert "happiness" in result.stdout


def test_cli_graph_exports_and_filters(monkeypatch, tmp_path: Path):
    from graphviz import Digraph

    def fake_render(self, filename: Optional[str] = None, cleanup: bool = True):  # type: ignore[no-redef]
        base = Path(filename or (tmp_path / "graph").as_posix())
        out_file = base.with_suffix("." + (self.format or "png"))
        out_file.write_bytes(b"")
        return str(out_file)

    monkeypatch.setattr(Digraph, "render", fake_render)

    img = tmp_path / "g.png"
    csv = tmp_path / "e.csv"
    jso = tmp_path / "g.json"

    result = runner.invoke(
        app,
        [
            "graph",
            "happy",
            "--depth",
            "1",
            "--out",
            str(img),
            "--csv-out",
            str(csv),
            "--json-out",
            str(jso),
            "-r",
            "synonym",
            "--min-degree",
            "1",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert img.exists()
    assert csv.exists()
    assert jso.exists()

    rows = [line.strip().split(",") for line in csv.read_text().splitlines() if line.strip()]
    assert rows[0] == ["source", "target", "relation"]
    rels = {r[2] for r in rows[1:]}
    assert rels.issubset({"synonym"})


def test_cli_graph_stopwords_and_exclude(monkeypatch, tmp_path: Path):
    from graphviz import Digraph

    def fake_render(self, filename: Optional[str] = None, cleanup: bool = True):  # type: ignore[no-redef]
        base = Path(filename or (tmp_path / "graph").as_posix())
        out_file = base.with_suffix("." + (self.format or "png"))
        out_file.write_bytes(b"")
        return str(out_file)

    monkeypatch.setattr(Digraph, "render", fake_render)

    stop = tmp_path / "stop.txt"
    stop.write_text("glad\n", encoding="utf-8")
    jso = tmp_path / "g.json"
    img = tmp_path / "g.svg"

    result = runner.invoke(
        app,
        [
            "graph",
            "happy",
            "--depth",
            "1",
            "--out",
            str(img),
            "--format",
            "svg",
            "--json-out",
            str(jso),
            "--stopwords",
            str(stop),
            "--exclude",
            "joyful",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert img.exists()
    data = json.loads(jso.read_text())
    names = {n["id"] for n in data["nodes"]}
    assert "glad" not in names
    assert "joyful" not in names


def test_cli_graph_rel_depth_and_pos_cap_flags(monkeypatch, tmp_path: Path):
    from graphviz import Digraph

    def fake_render(self, filename: Optional[str] = None, cleanup: bool = True):  # type: ignore[no-redef]
        base = Path(filename or (tmp_path / "graph").as_posix())
        out_file = base.with_suffix("." + (self.format or "png"))
        out_file.write_bytes(b"")
        return str(out_file)

    monkeypatch.setattr(Digraph, "render", fake_render)

    img = tmp_path / "g.pdf"
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
            "--format",
            "pdf",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert img.exists()
