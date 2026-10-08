"""Execute the baseline and extended English analysis notebooks."""
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
for name in sys.argv[1:] or ("sweetspot", "contact_analysis"):
    path = root / f"notebooks/{name}.ipynb"
    notebook = nbformat.read(path, as_version=4)
    NotebookClient(notebook, timeout=120, kernel_name="sweetspot",
                   resources={"metadata": {"path": str(root)}}).execute()
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(f"Notebook executed and validated: {name}", flush=True)
print("Outputs: results/sweetspot/, results/random_poses/ and results/combined/")
