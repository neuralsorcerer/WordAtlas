from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console
from rich.table import Table

from wordatlas.config import settings
from wordatlas.logging_config import configure_logging
from wordatlas.models import Relation
from wordatlas.services.graph_builder import build_graph
from wordatlas.services.renderer import to_graphviz

app = typer.Typer(add_completion=False, help="WordAtlas CLI")
console = Console()


@app.callback()
def _setup(
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable debug logging")] = False,
) -> None:
    configure_logging("DEBUG" if verbose else settings.log_level)


@app.command(name="list")
def list_relations(
    word: Annotated[str, typer.Argument(help="Center word")],
    depth: Annotated[
        int, typer.Option("--depth", min=0, help="Expansion depth")
    ] = settings.default_depth,
    max_nodes: Annotated[int, typer.Option("--max-nodes", help="Max nodes")] = settings.max_nodes,
    json_out: Annotated[
        Path | None, typer.Option("--json-out", help="Write graph JSON to file")
    ] = None,
) -> None:
    """List related words (prints a summary table, or dump JSON)."""
    g = build_graph(word, depth=depth, max_nodes=max_nodes)

    if json_out:
        json_out.write_text(json.dumps(g.model_dump(), indent=2))
        console.print(f"[green]Wrote[/green] {json_out}")
        raise typer.Exit(0)

    by_rel: dict[str, set[str]] = {
        "synonym": set(),
        "hypernym": set(),
        "hyponym": set(),
        "antonym": set(),
        "similar_to": set(),
    }
    for e in g.edges:
        by_rel[e.relation].add(e.target)

    table = Table(title=f"WordAtlas: {g.center} (depth={depth}, nodes={len(g.nodes)})")
    table.add_column("Relation")
    table.add_column("Examples")

    def take(s: set[str], n: int = 10) -> str:
        return ", ".join(sorted(list(s))[:n])

    for rel in ["synonym", "antonym", "hypernym", "hyponym", "similar_to"]:
        table.add_row(rel, take(by_rel[rel]))

    console.print(table)


@app.command()
def graph(
    word: Annotated[str, typer.Argument(help="Center word")],
    out: Annotated[Path, typer.Option("--out", help="Output image path (.png/.svg/.pdf)")] = Path(
        "graph.png"
    ),
    depth: Annotated[int, typer.Option("--depth", min=0)] = settings.default_depth,
    max_nodes: Annotated[int, typer.Option("--max-nodes")] = settings.max_nodes,
    relation: Annotated[
        list[str] | None,
        typer.Option(
            "--relation",
            "-r",
            help=("Filter relations (repeatable): synonym, antonym, hypernym, hyponym, similar_to"),
        ),
    ] = None,
    json_out: Annotated[
        Path | None, typer.Option("--json-out", help="Also write graph JSON to file")
    ] = None,
    open_after: Annotated[bool, typer.Option("--open", help="Open image after rendering")] = False,
    csv_out: Annotated[
        Path | None,
        typer.Option("--csv-out", help="Export edges CSV with columns source,target,relation"),
    ] = None,
    rel_depth: Annotated[
        list[str] | None,
        typer.Option(
            "--rel-depth", help="Per-relation depth like relation:depth, e.g. synonym:1,hypernym:2"
        ),
    ] = None,
    pos_cap: Annotated[
        list[str] | None,
        typer.Option("--pos-cap", help="Per-POS caps like pos:cap, e.g. n:50,a:30"),
    ] = None,
    exclude: Annotated[
        list[str] | None, typer.Option("--exclude", help="Exclude nodes/words (repeatable)")
    ] = None,
    stopwords: Annotated[
        Path | None, typer.Option("--stopwords", help="Path to newline-separated words to exclude")
    ] = None,
    fmt: Annotated[
        str | None,
        typer.Option(
            "--format", help="Render format (png/svg/pdf). Defaults to inferred from --out"
        ),
    ] = None,
    min_degree: Annotated[
        int,
        typer.Option(
            "--min-degree", min=0, help="Drop nodes with total degree < N (center is kept)"
        ),
    ] = 0,
) -> None:
    """Render Graphviz image for the word graph."""

    allowed_keys: set[Relation] = cast(
        set[Relation], set(["synonym", "antonym", "hypernym", "hyponym", "similar_to"])
    )

    # Parse rel-depth and pos-cap inputs
    rel_depths_parsed: dict[Relation, int] = {}
    if rel_depth:
        for item in rel_depth:
            try:
                k, v = item.split(":", 1)
                if k not in allowed_keys:
                    allowed_str = ", ".join(sorted(allowed_keys))
                    raise typer.BadParameter(
                        f"Unknown relation '{k}' in --rel-depth; allowed: {allowed_str}"
                    )
                rel_depths_parsed[cast(Relation, k)] = max(0, int(v))
            except ValueError as err:
                raise typer.BadParameter(
                    f"Invalid --rel-depth '{item}', expected relation:int"
                ) from err

    pos_caps: dict[str, int] = {}
    if pos_cap:
        for item in pos_cap:
            try:
                k, v = item.split(":", 1)
                pos_caps[k] = max(0, int(v))
            except ValueError as err:
                raise typer.BadParameter(
                    f"Invalid --pos-cap '{item}', expected pos:int (e.g. n:50)"
                ) from err

    # Build exclude set
    excl: set[str] = set(x.strip().lower() for x in (exclude or []))
    if stopwords and stopwords.exists():
        try:
            for line in stopwords.read_text(encoding="utf-8").splitlines():
                w = line.strip().lower()
                if w:
                    excl.add(w)
        except Exception:
            # ignore stopword file read errors
            pass

    g = build_graph(
        word,
        depth=depth,
        max_nodes=max_nodes,
        rel_depths=rel_depths_parsed or None,
        pos_caps=pos_caps or None,
        exclude=excl or None,
    )

    allowed: set[str] | None = None
    if relation:
        invalid = [r for r in relation if r not in allowed_keys]
        if invalid:
            allowed_str = ", ".join(sorted(allowed_keys))
            raise typer.BadParameter(
                f"Unknown --relation values: {', '.join(invalid)}; allowed: {allowed_str}"
            )
        allowed = set(relation)

    # Optional filtering before rendering/exports
    if allowed is not None:
        g.edges = [e for e in g.edges if e.relation in allowed]
    if min_degree > 0:
        deg: dict[str, int] = {}
        for e in g.edges:
            deg[e.source] = deg.get(e.source, 0) + 1
            deg[e.target] = deg.get(e.target, 0) + 1
        keep_nodes: set[str] = {
            n.id for n in g.nodes if (n.id == g.center or deg.get(n.id, 0) >= min_degree)
        }
        g.nodes = [n for n in g.nodes if n.id in keep_nodes]
        g.edges = [e for e in g.edges if e.source in keep_nodes and e.target in keep_nodes]

    # Determine format
    inferred = out.suffix.replace(".", "")
    if fmt:
        fmt = fmt.lower()
        if fmt not in {"png", "svg", "pdf"}:
            raise typer.BadParameter("--format must be one of: png, svg, pdf")
        render_fmt = fmt
    else:
        render_fmt = inferred or "png"

    dot = to_graphviz(g, allowed_relations=None)  # relations already filtered above
    out.parent.mkdir(parents=True, exist_ok=True)
    filename_no_ext = str(out.with_suffix(""))
    dot.format = render_fmt
    dot.render(filename=filename_no_ext, cleanup=True)

    # Compute actual written path, accounting for possible format override
    if out.suffix:
        if render_fmt and out.suffix.lstrip(".") != render_fmt:
            written = out.with_suffix("." + render_fmt)
        else:
            written = out
    else:
        written = out.with_suffix("." + render_fmt)

    if json_out:
        json_out.write_text(json.dumps(g.model_dump(), indent=2))

    if csv_out:
        import csv

        with csv_out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "relation"])
            for e in g.edges:
                writer.writerow([e.source, e.target, e.relation])

    console.print(f"[green]Wrote[/green] {written}")

    if open_after:
        try:
            import os
            import platform
            import webbrowser

            if platform.system() == "Windows":
                startfile = getattr(os, "startfile", None)
                if callable(startfile):
                    startfile(str(written))
            elif platform.system() == "Darwin":
                os.system(f"open '{written}'")
            else:
                os.system(f"xdg-open '{written}' >/dev/null 2>&1 &")
        except Exception:
            try:
                webbrowser.open(str(written))
            except Exception:
                pass


@app.command()
def show(
    word: Annotated[str, typer.Argument(help="Center word")],
    depth: Annotated[int, typer.Option("--depth", min=0)] = settings.default_depth,
    max_nodes: Annotated[int, typer.Option("--max-nodes")] = settings.max_nodes,
) -> None:
    """Quickly print a compact JSON with node/edge counts and a few examples."""
    g = build_graph(word, depth=depth, max_nodes=max_nodes)
    console.print(
        {
            "center": g.center,
            "nodes": len(g.nodes),
            "edges": len(g.edges),
            "sample": [e.model_dump() for e in g.edges[:10]],
        }
    )


@app.command()
def web(
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8000,
    reload: Annotated[bool, typer.Option("--reload", help="Auto-reload (dev)")] = False,
) -> None:
    """Run the FastAPI server with static UI."""
    import uvicorn

    uvicorn.run("wordatlas.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":  # pragma: no cover
    app()
