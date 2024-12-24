"""
Script to check the line count of python files
and print files with more than 500 lines with their line count.

Mainly intended for avoiding too large files.
"""

from pathlib import Path

for file in Path("src").glob("**/*.py"):
    line_count: int = len(file.read_text(errors="ignore").splitlines())
    if line_count > 500:
        print(file, line_count)
