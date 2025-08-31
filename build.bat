@echo off
call update_lupdate_file.bat
call update_qts.bat
call compile_qts.bat
call compile_qrc.bat
uv run scripts\build.py
