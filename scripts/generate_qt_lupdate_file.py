# type: ignore
"""
Script to generate Qt project file for pyside6-lupdate.

Original Code from:
    https://github.com/trin94/PySide6-project-template/blob/main/build-aux/generate-lupdate-project-file.py

Licensed under:
    GNU General Public License 3.0
"""

import argparse
import json
import sys
from pathlib import Path


class ArgumentValidator:
    _errors = []

    def validate_named_directory(self, directory: Path, *, name: str):
        if not directory.exists():
            self._errors.append(f"{name.capitalize()} {directory} does not exist")
        elif not directory.is_dir():
            self._errors.append(f"{name.capitalize()} {directory} is not a directory")

    def validate_directory(self, directory: Path):
        if not directory.exists():
            self._errors.append(f"Directory {directory} does not exist")
        elif not directory.is_dir():
            self._errors.append(f"Directory {directory} is not a directory")

    def validate_directories(self, directories: list[Path]):
        for directory in directories:
            self.validate_directory(directory)

    def validate_files(self, files: list[Path]):
        for file in files:
            self._validate_file(file)

    def _validate_file(self, file: Path):
        if not file.exists():
            self._errors.append(f"File {file} does not exist")
        elif not file.is_file():
            self._errors.append(f"File {file} is not a file")

    def _validate_translation(self, translation: Path):
        if not translation.parent.exists():
            self._errors.append(f"Directory {translation.parent} does not exist")
        elif not translation.parent.is_dir():
            self._errors.append(f"Directory {translation.parent} is not a directory")

    def validate_translations(self, translations: list[Path]):
        for translation in translations:
            self._validate_translation(translation)

    def break_on_errors(self):
        if errors := self._errors:
            for error in errors:
                print(error, file=sys.stderr)
            sys.exit(1)


class ProjectFileGenerator:
    _extensions_included = {".py"}
    _extensions_translation = ".ts"
    _files: list[Path] = []
    _translations: list[Path] = []

    def __init__(self, root_dir: Path):
        self._root_dir = root_dir

    def add(self, directories: list[Path], files: list[Path]):
        for directory in directories:
            for path in directory.rglob("*"):
                if path.is_file():
                    self._files.append(path)
        self._files.extend(files)

    def add_translations(self, translations: list[Path]):
        self._translations.extend(translations)

    def make_files_relative(self):
        self._files = [path.relative_to(self._root_dir) for path in self._files]

    def remove_irrelevant_files(self):
        self._files = [
            path for path in self._files if path.suffix in self._extensions_included
        ]

    def sort_files(self):
        self._files = sorted(self._files)

    def generate_project_file(self, file: Path):
        files = [
            str(path)
            for path in self._files
            if path.suffix != self._extensions_translation
        ]
        translations = [
            str(path.relative_to(self._root_dir))
            for path in self._files + self._translations
            if path.suffix == self._extensions_translation
        ]
        structure = {
            "excluded": [],
            "includePaths": [],
            "projectFile": "",
            "sources": files,
            "translations": translations,
        }
        data = json.dumps([structure], indent=2, sort_keys=True)
        file.write_text(data, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create a json project file")
    parser.add_argument(
        "--relative-to",
        type=str,
        required=True,
        help="Root directory to make files relative to",
    )
    parser.add_argument(
        "--include-directory",
        type=str,
        action="append",
        default=[],
        help="Directory to include. Can be used multiple times",
    )
    parser.add_argument(
        "--include-file",
        type=str,
        action="append",
        default=[],
        help="File to include. Can be used multiple times",
    )
    parser.add_argument(
        "--add-translation",
        type=str,
        action="append",
        default=[],
        help="Add translation file to be created.",
    )
    parser.add_argument(
        "--out-file",
        type=str,
        required=True,
        help="Path of the json project file to generate",
    )
    run(parser.parse_args())


def run(args):
    root_dir = Path(args.relative_to).absolute()
    out_file = Path(args.out_file)
    directories = [Path(path).absolute() for path in args.include_directory]
    files = [Path(path).absolute() for path in args.include_file]
    translations = [Path(path).absolute() for path in args.add_translation]

    validator = ArgumentValidator()
    validator.validate_named_directory(root_dir, name="Root directory")
    validator.validate_directories(directories)
    validator.validate_files(files)
    validator.validate_translations(translations)
    validator.break_on_errors()

    generator = ProjectFileGenerator(root_dir=root_dir)
    generator.add(directories, files)
    generator.add_translations(translations)
    generator.make_files_relative()
    generator.remove_irrelevant_files()
    generator.sort_files()
    generator.generate_project_file(file=out_file)


if __name__ == "__main__":
    main()
