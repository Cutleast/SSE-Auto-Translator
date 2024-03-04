<p align="center">
<!-- <img src="https://i.imgur.com/9Z2Nnrf.png" width="500px" /> -->
Placeholder for header image
<br>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/111491"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<br>

# Description

This is a tool for translating whole modlists with relative ease. It automatically scans your modlist for required translations by using AI-based language detection.
SSE-AT then scans the original mods on Nexus Mods for available translations and downloads them (automated downloads only for Nexus Mods Premium users).
SSE-AT manages all installed translations in a combined database and makes use of the Dynamic String Distributor SKSE plugin to inject the translations
into the game without modifications to any plugins or "downgrading" the original plugins in case of outdated translations.
The tool also has an built-in editor for creating and editing translations yourself and supports Google Translator and DeepL APIs.

# Features
- Automated detection of required and already installed translations
- Automated scan for required translations on Nexus Mods
- Version-independent translations via SKSE
- Combined Database to auto-translate plugins that only persist of Vanilla strings
- Built-in Editor for creating and editing translations
  - Search and Replace Feature
  - Built-in support for Google Translator (free) and DeepL API (API Key required)
  - Export Feature to share own translations
- Import Feature for manually installing translations and exported xTranslator translations (in XML format only)
- Ignore-List Feature to completely ignore plugins that are falsely marked as "Translation Required"
- Built-in Documentation
- Deep Scan Feature to find incomplete translations
- Startup-Dialog for easy setup and introduction
- Status colors to quickly give an overview of the translation state of your modlist

# Contributing

## 1. Feedback (Suggestions/Issues)

If you encountered an issue/error or you have a suggestion, create an issue under the "Issues" tab above.

## 2. Code contributions

### 1. Install requirements

1. Install Python 3.11 (Make sure that you add it to PATH!)
2. Clone repository
3. Open terminal in repository folder
4. Type in following command to install all requirements (Using a virtual environment is strongly recommended!):
   `pip install -r requirements.txt`

### 2. Execute from source

1. Open terminal in src folder
2. Execute main file
   `python app.py`

### 3. Compile and build executable

1. Follow the steps on this page [Nuitka.net](https://nuitka.net/doc/user-manual.html#usage) to install a C Compiler
2. Run `build.bat` with activated virtual environment from the root folder of this repo.
3. The executable and all dependencies are built in the main.dist-Folder.

# Credits

- Qt by [The Qt Company Ltd](https://qt.io)
- [lingua-py](https://github.com/pemistahl/lingua-py) by [Peter M. Stahl](https://github.com/pemistahl)
- [DynamicStringDistributor](https://github.com/SkyHorizon3/DynamicStringDistributor) by [SkyHorizon](https://github.com/SkyHorizon3)
- Icon by [Wuerfelhusten](https://nexusmods.com/users/122160268)
