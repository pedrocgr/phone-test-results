"""Execute the English Sweet Spot notebook from the repository root."""
from pathlib import Path

import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parent
path = root / "sweetspot_analysis.ipynb"
notebook = nbformat.read(path, as_version=4)
NotebookClient(notebook, timeout=120, kernel_name="sweetspot",
               resources={"metadata": {"path": str(root)}}).execute()
nbformat.validate(notebook)
nbformat.write(notebook, path)
print("Notebook executed and validated. Outputs: sweetspot_analysis/")
