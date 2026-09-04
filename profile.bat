@echo off
uv run python -m cProfile -o .\profile_result.pstats .\src\main.py %*
uv run python -c "import pstats; pstats.Stats('profile_result.pstats').strip_dirs().sort_stats('cumtime').print_stats(80)"
