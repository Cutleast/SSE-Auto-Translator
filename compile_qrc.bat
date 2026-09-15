@echo off
uv run --directory core-lib python scripts\compile_resources.py
uv run pyside6-rcc res\resources.qrc -o src\resources_rc.py
