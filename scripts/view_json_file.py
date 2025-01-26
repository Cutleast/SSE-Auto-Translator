"""
Script to view a JSON file in a specialized QTreeView with lazy loading for huge files.
"""

import json
import os
import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ui.widgets.json_data_view.json_data_view import JsonDataView

if __name__ == "__main__":
    app = QApplication()

    widget = JsonDataView()
    widget.show()
    widget.resize(800, 600)

    json_file_path = Path(sys.argv[-1])

    start: float = time.time()
    print("Loading JSON file...")
    with json_file_path.open("rb") as f:
        data = json.load(f)
    print(f"Loaded JSON file in {time.time() - start:.2f} seconds.")

    widget.set_data(data)

    app.exec()
