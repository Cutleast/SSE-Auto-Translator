<p align="center">
<img src="https://i.imgur.com/exiipaG.png" width="1000px" />
<br>
<a href="https://discord.gg/pqEHdWDf8z"><img src="https://i.imgur.com/WnwiiNQ.png" height="60px"/> </a>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/111491"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<a href="https://trello.com/b/AA2KwhH8/sse-auto-translator"><img src="https://i.imgur.com/sIjqMOg.png" height="60px"/> </a>
<br>
</p>

# Description

This tool allows you to translate entire modlists with relatively little effort. It utilizes AI-based language detection to automatically identify necessary translations in your modlist.
The tool then searches for available translations of the original mods on Nexus Mods and downloads them (automated downloads are exclusively available for Nexus Mods Premium users).
SSE-AT manages all installed translations in a single database and injects them into the game using the Dynamic String Distributor SKSE plugin, without modifying any plugins or "downgrading" the original plugins in case of outdated translations.
Additionally, the tool also features a built-in editor for creating and editing translations yourself and has support for Google Translator and DeepL API.

# Usage

See [Documentation](/doc/Instructions_en_US.md).

# Features

- Automated detection of required translations
- Automated detection and import of already installed translations
- Automated scan for required translations on Nexus Mods
- Version-independent translations via SKSE
- Combined Database to auto-translate plugins that are completely covered by Vanilla strings or other installed translations
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
- Supports Mod Organizer 2 and Vortex
- Bind to "Mod Manager Download" Buttons at Nexus Mods to conveniently download translations from Nexus Mods (especially for free users)
  - this requires manual activation in the "Translations" tab
  - "Auto-bind" is available in settings (experimental)
    - with this enabled, SSE-AT gets auto-linked to Mod Manager Downloads on startup and unlinked when closed
    - experimental, because a crash might prevent unlinking

# Limitations

- Only Plugin Files (.esp, .esm and .esl) are supported at the moment
  - this means that there is no support for sound files, interface translations (data/interface/*.txt) or Papyrus scripts (.pex), etc.
- Translations that are not on a separate modpage and/or linked (under "Translations") on the original modpage cannot be found by SSE-AT
  - for eg. the german translation for [Unofficial Skyrim Modder&#39;s Patch](https://www.nexusmods.com/skyrimspecialedition/mods/49616?tab=files)
  - those have to be installed manually in SSE-AT by either downloading and importing them or by starting the download via SSE-AT itself (see [Documentation](/doc/Instructions_en_US.md) for more)

# FAQ

#### Do I have to edit any ini files?

- Make sure to set *[General]* > *sLanguage* in *Skyrim.ini* to your desired language (for eg. *GERMAN*)
- Since sound is not supported I also recommend setting the english voice files in the same ini file. Just go to *[Archive]* and under *sResourceArchiveList2 replace Voices_xx0.bsa* with *Voices_en0.bsa*

#### SSE-AT detected a plugin (or multiple) as *Translation Required* although it contains no visible strings. What can I do to prevent it from detecting it again?

- You can add it to the ignore list like this: Right Click the plugin(s) > "Add to Ignore List"
- This prevents SSE-AT from including it at all
- You can view and remove plugins from the Ignore List via the "Ignore List" Button right next to the filter button at the top

#### There are still untranslated strings in my game. I thought SSE-AT fixes this?

- SSE-AT can only download translations available on Nexus Mods and auto-create translations for mods that are entirely covered by already installed translations (including vanilla strings).
- Depending on your desired language, there are more or less available translations at Nexus Mods

#### I found untranslated strings from a mod that has a translation installed.

- Please ensure that the original translation works and that it's a problem with SSE-AT before opening a Bug report or Issue

#### What about [SSE-LD](https://www.nexusmods.com/skyrimspecialedition/mods/106185)? Will it be taken down or discontinued?

- While SSE-AT is able to scan Plugin files (.esp, .esm, .esl) just like SSE-LD, it does not support Papyrus Scripts (.pex) or MCM translations (.txt) at the moment.
- SSE-LD will remain online for the time being, but don't expect any major updates or changes other than some bug fixes.
- As soon as SSE-AT supports extraction of non-plugin files from translations, SSE-LD will be completely discontinued and the GitHub repo will be archived (but stay public).

# Contributing

## 1. Feedback (Suggestions/Issues)

If you encountered an issue/error or you have a suggestion, create an issue under the "Issues" tab above.

## 2. Code contributions

### 1. Install requirements

1. Install Python 3.11 (Make sure that you add it to PATH!)
2. Clone repository
3. Open terminal in repository folder
4. Create a virtual environment and activate it by running following command:
   `python -m venv .venv`
5. Type in following command to install all requirements:
   `pip install -r requirements.txt`

### 2. Execute from source

1. Open terminal in src folder
2. Execute main file
   `python app.py`

### 3. Compile and build executable

1. Run `build.bat` with activated virtual environment from the root folder of this repo.
2. The executable and all dependencies are built in the main.dist-Folder.

## 3. Beta-Testing

If you are interested in testing pre-release versions of SSE-AT, join our Discord server above.

# Credits

- Qt by [The Qt Company Ltd](https://qt.io)
- [lingua-py](https://github.com/pemistahl/lingua-py) by [Peter M. Stahl](https://github.com/pemistahl)
- [Nuitka](https://github.com/Nuitka/Nuitka)
- [DynamicStringDistributor](https://github.com/SkyHorizon3/SSE-Dynamic-String-Distributor) by [SkyHorizon](https://github.com/SkyHorizon3)
- Icon by [Wuerfelhusten](https://nexusmods.com/users/122160268)
