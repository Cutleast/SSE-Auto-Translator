<p align="center">
<img src="https://i.imgur.com/exiipaG.png" width="1000px" />
<br>
<a href="https://discord.gg/pqEHdWDf8z"><img src="https://i.imgur.com/VMdA0q7.png" height="60px"/> </a>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/111491"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://docs.moddingforge.com/sse-at"><img src="https://i.imgur.com/NFNG8Tb.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<br>
</p>

## Description

SSE Auto Translator is an independent Windows app that allows you to translate entire mod lists with a high degree of automation. Its main features include an automatic mod list scan that identifies the mods that need translation. SSE-AT is then able to automatically search [Nexus Mods](https://www.nexusmods.com/) (and [La Confrérie des Traducteurs](https://www.confrerie-des-traducteurs.fr/) for French translations) for available translations, download them, and convert them to DSD format. The downloaded translations are then combined into a new mod (the so-called Output Mod) and installed at the end of your mod list. In addition, SSE Auto Translator offers an integrated editor that can be used to edit downloaded translations and create new ones.

## Usage

See [Documentation > Quick Start & Basic Usage](https://docs.moddingforge.com/sse-at/quick_start.html).

## Features

See [Documentation > Introduction](https://docs.moddingforge.com/sse-at/index.html#_features) for a full list of features.

## Limitations

See [Documentation > Introduction](https://docs.moddingforge.com/sse-at/index.html#_limitations) for a full list of limitations.

## FAQ

See [Documentation > FAQs](https://docs.moddingforge.com/sse-at/faqs.html) for a full list of frequently asked questions.

## Contributing

### 1. Feedback (Suggestions/Issues)

If you encountered an issue/error or you have a suggestion, create an issue under the "Issues" tab above.

### 2. Code contributions

#### 1. Install requirements

1. Install [Python 3.12](https://www.python.org/downloads/) (Make sure that you add it to PATH!)
2. Install [uv](https://github.com/astral-sh/uv#installation)
3. Clone repository and all submodules with `git clone https://github.com/Cutleast/SSE-Auto-Translator --recurse-submodules`
4. Open terminal in repository folder
5. Run the following command to init your local environment and to install all dependencies: `uv sync`
6. Run the following command to build SSE-AT and compile the required resource file: `build.bat`

#### 2. Execute from source

1. Open terminal in repository folder
2. Execute main file with uv: `uv run src\main.py`

#### 3. Compile and build executable

1. Run `build.bat` from the root folder of this repo.
2. The executable and all dependencies are built in the `dist/SSE-AT`-Folder and gets packed in a `dist/SSE-AT v[version].zip`.

### 3. Beta-Testing

If you are interested in testing pre-release versions of SSE-AT, join our Discord server above.

### 4. Maintaining a Masterlist

If you're interested in maintaining a masterlist for your language, contact us (@cutleast or @whusten) on our Discord server linked above!

## Credits

- Qt by [The Qt Company Ltd](https://qt.io)
- [lingua-py](https://github.com/pemistahl/lingua-py) by [Peter M. Stahl](https://github.com/pemistahl)
- [Nuitka](https://github.com/Nuitka/Nuitka)
- [DynamicStringDistributor](https://github.com/SkyHorizon3/SSE-Dynamic-String-Distributor) by [SkyHorizon](https://github.com/SkyHorizon3)
- Icon by [Wuerfelhusten](https://nexusmods.com/users/122160268)
- Editor QoL Improvements by [FuchieSteph](https://github.com/FuchieSteph)
- Other used software and libraries:
  - Open SSE-AT > Help > About > Used Software
  - Alternatively: [licenses.py](./src/core/utilities/licenses.py)
- Test data used (only distributed with the source code and used for automated tests in [tests](./tests/)):
  - [Obsidian Weathers and Seasons](https://www.nexusmods.com/skyrimspecialedition/mods/12125) by [DrJacopo](https://next.nexusmods.com/profile/DrJacopo)
  - [Obsidian Weathers and Seasons - German](https://www.nexusmods.com/skyrimspecialedition/mods/16286) by [Hilli1](https://next.nexusmods.com/profile/Hilli1)
  - [Ordinator - Perks of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1137) by [Enai Siaion](https://next.nexusmods.com/profile/EnaiSiaion)
  - [RS Children Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/2650) by [isophe](https://next.nexusmods.com/profile/isophe)
  - [Wet and Cold SE](https://www.nexusmods.com/skyrimspecialedition/mods/644) by [StepModifications](https://next.nexusmods.com/profile/StepModifications)
  - [Wet and Cold SE - German](https://www.nexusmods.com/skyrimspecialedition/mods/89391) by [kroenel](https://next.nexusmods.com/profile/kroenel)
  - `_ResourcePack.esl & _ResourcePack.bsa` by Bethesda from the Vanilla base game, stripped down to the bare minimum
