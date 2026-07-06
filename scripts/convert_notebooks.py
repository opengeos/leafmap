#!/usr/bin/env python
"""Convert documentation notebooks to Markdown pages for the Zensical build.

Zensical does not yet support the mkdocs-jupyter plugin, so this script is
run before ``zensical build`` to convert every notebook under ``docs/`` into
a Markdown page that Zensical can render natively. Stored cell outputs are
preserved, and extracted images are written to a ``<notebook>_files``
directory next to the generated Markdown file. The original ``.ipynb`` files
are left in place so that they are still copied to the built site and remain
downloadable.

Usage:
    python scripts/convert_notebooks.py
"""

import concurrent.futures
import pathlib
import sys

import nbformat
from nbconvert import MarkdownExporter
from nbconvert.writers import FilesWriter

DOCS_DIR = pathlib.Path(__file__).resolve().parents[1] / "docs"
NOTEBOOK_DIRS = ["notebooks", "workshops", "maplibre"]


def convert_notebook(path: pathlib.Path) -> str:
    """Convert a single notebook to a Markdown page next to it.

    Args:
        path: Path to the ``.ipynb`` file to convert.

    Returns:
        str: The path of the notebook that was converted, for logging.
    """
    notebook = nbformat.read(str(path), as_version=4)
    # Many notebooks are saved without language_info metadata, which nbconvert
    # needs to emit language-tagged code fences for syntax highlighting.
    notebook.metadata.setdefault("language_info", {"name": "python"})
    exporter = MarkdownExporter(exclude_input_prompt=True, exclude_output_prompt=True)
    resources = {"output_files_dir": f"{path.stem}_files", "unique_key": path.stem}
    body, resources = exporter.from_notebook_node(notebook, resources=resources)
    writer = FilesWriter(build_directory=str(path.parent))
    writer.write(body, resources, notebook_name=path.stem)
    return str(path.relative_to(DOCS_DIR))


def main() -> None:
    """Convert all notebooks in the documentation folders to Markdown."""
    notebooks = sorted(
        nb for folder in NOTEBOOK_DIRS for nb in (DOCS_DIR / folder).glob("*.ipynb")
    )
    if not notebooks:
        sys.exit("No notebooks found to convert.")

    failures = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(convert_notebook, nb): nb for nb in notebooks}
        for future in concurrent.futures.as_completed(futures):
            nb = futures[future]
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                failures.append((nb, exc))
                print(f"FAILED: {nb}: {exc}", file=sys.stderr)

    print(f"Converted {len(notebooks) - len(failures)}/{len(notebooks)} notebooks.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
