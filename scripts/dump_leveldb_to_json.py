"""
Copyright (c) Cutleast

Script to dump a Vortex database to a JSON file.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.utilities.leveldb import LevelDB


def run(args: argparse.Namespace) -> None:
    db_path = Path(args.db_path or os.getenv("APPDATA") + "/Vortex/state.v2")  # type: ignore[operator]
    out_file = Path(args.out_file or "state.v2.json")
    prefix: str | None = args.prefix

    print(f"Dumping prefixed data '{prefix}' from '{db_path}' to '{out_file}'...")

    level_db = LevelDB(db_path)
    data = level_db.load(prefix=prefix)

    with out_file.open("w", encoding="utf-8") as file:
        file.write(json.dumps(data, indent=4))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dumps a Vortex database to a JSON file."
    )
    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to the Vortex database. Defaults to %APPDATA%/Vortex/state.v2.",
    )
    parser.add_argument(
        "--out-file",
        type=str,
        help="Path to the output file. Defaults to state.v2.json.",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        help="Prefix to filter the database. Defaults to empty.",
    )

    run(parser.parse_args())


if __name__ == "__main__":
    main()
