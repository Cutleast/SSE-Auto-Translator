"""
Name: SSE Auto Translator
Author: Cutleast
License: Attribution-NonCommercial-NoDerivatives 4.0 International
Python Version: 3.11.2
Qt Version: 6.6.1
"""

import sys

from app import MainApp

args: list[str] = sys.argv[1:]

print(f"{args = }")


if len(args):
    match args[0]:
        case "--download":
            if args[-1].startswith("nxm://"):
                from nxm_handler import handle

                handle()
            else:
                print("Missing Download URL!")

        case "--bind-nxm":
            import winreg

            REG_PATH = "nxm\\shell\\open\\command"
            REG_VALUE = f'"{MainApp.executable}" --download "%1"'

            try:
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, REG_PATH) as hkey:
                    winreg.SetValue(hkey, "", winreg.REG_SZ, REG_VALUE)

                sys.exit(0)

            except OSError:
                sys.exit(1)

        case "--show-docs":
            app = MainApp()
            app.show_documentation_standalone()

            sys.exit(0)

        case "--extract-strings":
            from pathlib import Path

            plugin_path = Path(args[-1])

            if not plugin_path.is_file():
                print(f"{str(plugin_path)!r} is not an existing file!")
                sys.exit(1)

            if plugin_path.suffix.lower() in [".esp", ".esl", ".esm"]:
                import json

                import utilities
                from plugin_parser import PluginParser

                output_path = plugin_path.with_suffix(f"{plugin_path.suffix}.json")

                parser = PluginParser(plugin_path)
                strings = [
                    string.to_string_data()
                    for group in parser.extract_strings().values()
                    for string in group
                ]

                with output_path.open("w", encoding="utf8") as output_file:
                    json.dump(strings, output_file, indent=4, ensure_ascii=False)

                print(f"Strings written to {str(output_path)!r}.")

                sys.exit(0)

        case "--help":
            print(
                "--download <NXM URL>                      Starts download of file at given URL"
            )
            print(
                "--show-docs                               Opens Documentation without starting Main Application."
            )
            print(
                "--bind-nxm                                Binds Mod Manager Downloads to SSE-AT. Mainly used for Admin Rights"
            )
            print(
                "--extract-strings <Path to Plugin File>   Extracts Strings from Plugin and writes them in a JSON file with the same location and name."
            )

            sys.exit(0)

        case "--version":
            print(f"{MainApp.name} v{MainApp.version} by Cutleast")
            print()
            print(
                "Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International"
            )

            sys.exit(0)

MainApp().exec()
