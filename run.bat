@echo off
call update_lupdate_file.bat
call update_qts.bat
call compile_qts.bat
call compile_qrc.bat
if not exist webview2-helper\bin uv run scripts\build_webview2_helper.py
uv run src\main.py
