<p align="center">
<!-- <img src="https://i.imgur.com/9Z2Nnrf.png" width="500px" /> -->
Placeholder for header image
<br>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/111491"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<br>

# Description

This tool allows you to translate entire modlists with relatively little effort. It utilizes AI-based language detection to automatically identify necessary translations in your modlist.
The tool then efficiently searches for available translations of the original mods on Nexus Mods and downloads them (automated downloads are exclusively available for Nexus Mods Premium users).
SSE-AT manages all installed translations in a single database and injects them into the game using the Dynamic String Distributor SKSE plugin, without modifying any plugins or "downgrading" the original plugins in case of outdated translations.
Additionally, the tool also features a built-in editor for creating and editing translations yourself and has support for Google Translator and DeepL API.

# Usage
See [Documentation](/doc/Instructions_en_US.md).

# Features

- Automated detection of required translations
- Automated detection and import of already installed translations
- Automated scan for required translations on Nexus Mods
- Version-independent translations via SKSE
- Combined Database to auto-translate plugins that only persist of Vanilla strings
- Built-in Editor for creating and editing translations
  - Search and Replace Feature
  - Built-in support for Google Translator (free) and DeepL API (API Key required)
  - Export Feature to share own translations
- Import Feature for manually installing translations and exported (XML format only) xTranslator translations
- Ignore-List Feature to completely ignore plugins that are falsely marked as "Translation Required"
- Built-in Documentation
- Deep Scan Feature to find incomplete translations
- Startup-Dialog for easy setup and introduction
- Status colors to quickly give an overview of the translation state of your modlist
- Bind to "Mod Manager Download" Buttons at Nexus Mods to conveniently download translations from Nexus Mods (especially for free users)
  - this requires manual activation in the "Translations" tab
  - "Auto-bind" is available in settings (experimental)
    - with this enabled, SSE-AT gets auto-linked to Mod Manager Downloads on startup and unlinked when closed
    - experimental, because a crash might prevent unlinking

# Limitations

- Only Plugin Files (.esp, .esm and .esl) are supported at the moment
  - this means that there is no support for sound files, interface translations (data/interface/*.txt) or Papyrus scripts (.pex)
- Translations that are not on a separate modpage and/or linked (under "Translations") on the original modpage cannot be found by SSE-AT
  - for eg. the german translation for [Unofficial Skyrim Modder's Patch](https://www.nexusmods.com/skyrimspecialedition/mods/49616?tab=files)
  - those have to be installed manually in SSE-AT by either downloading and importing them or by starting the download via SSE-AT itself (see [FAQ](#faq) below for more)

# FAQ

#### SSE-AT detected a plugin (or multiple) as *Translation Required* although it contains no visible strings. What can I do to prevent it from detecting it again?

- You can add it to the ignore list like this: Right Click the plugin(s) > "Add to Ignore List"
- This prevents SSE-AT from including it at all
- You can view and remove plugins from the Ignore List via the "Ignore List" Button right next to the filter button at the top

#### There are still untranslated strings in my game. I thought SSE-AT fixes this?

- SSE-AT can only download translations available on Nexus Mods and auto-create translations for mods that are entirely covered by already installed translations (including vanilla strings).
- Depending on your desired language, there are more or less available translations at Nexus Mods

#### I found untranslated strings from a mod that has a translation installed.

- Please ensure that the original translation works and that it's a problem with SSE-AT before opening a Bug report or Issue

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
