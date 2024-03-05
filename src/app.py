"""
Name: SSE Auto Translator
Author: Cutleast
License: Attribution-NonCommercial-NoDerivatives 4.0 International
Python Version: 3.11.2
Qt Version: 6.6.1
"""

import sys

sys.argv.pop(0)

print(f"{sys.argv = }")

if len(sys.argv) >= 2:
    if sys.argv[0] == "--download" and sys.argv[1].startswith("nxm://"):
        from nxm_handler import handle

        handle()

elif len(sys.argv) >= 1:
    if sys.argv[0] == "--bind-nxm":
        import winreg

        from main import MainApp

        REG_PATH = "nxm\\shell\\open\\command"
        REG_VALUE = f'"{MainApp.executable}" --download "%1"'

        try:
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, REG_PATH) as hkey:
                winreg.SetValue(hkey, "", winreg.REG_SZ, REG_VALUE)

            sys.exit(0)

        except OSError:
            sys.exit(1)
    elif sys.argv[0] == "--show-docs":
        from main import MainApp

        app = MainApp()
        app.show_documentation_standalone()

        sys.exit(0)

from main import main

main()
