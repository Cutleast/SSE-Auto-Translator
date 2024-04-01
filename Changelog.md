# v1.1.0

##### This Update requires a complete wipe of your existing SSE-AT data!! This is a one-time only and we think the advantages outweigh the disadvantages.

### Highlights

- Add Updates Feature for Database
  - Updates for translations from Nexus Mods can now be checked and downloaded from within SSE-AT
- Add Masterlist Feature for special cases
  - This feature can always be disabled in Settings > User Settings
  - IgnoreList Dialog now has a tab for base game plugins and Masterlist
  - Masterlist is hosted in GitHub repository
  - At time of writing, only a german masterlist is provided and **we need people to maintain masterlists for other languages** as well
  - If you want to maintain a masterlist for a language or you know of translations that are on Nexus Mods but are not visible in the translations of the original mod then please join our Discord and tell us
  - An example for this can be found in the Optional Files of Unofficial Skyrim Modder's Patch where its german translation is
- Improve visual style
  - Overhauled Stylesheet and reduced accent color "bloat" ;)
  - Add Translation Counter to Translations Panel
  - Relevant buttons are now highlighted
  - TranslatorDialog now auto-focuses StringEntry
  - Change icon for "Show Strings"
  - StringListDialog and Translation Editor now use monospace font for Editor ID, FormID and Type columns
- Major Overhaul of Plugin Parser and DSD Format
  - eg. FormIDs are now separate, include the name of the respective master plugin and are required for every string
    - due to this, xTranslator import had to be removed
  - For a list of complete changes, see Documentation at DSD repository
  - This fixes a lot of potential issues like mismatching of translation and original strings or not replacing of strings ingame
  - This also fixes several decoding errors previously happening in some plugins
  - **Old translations have to be ported by following these steps for each plugin**
    1. Export the translation
    2. Delete translation from database
    3. Scan plugin so that it's marked as *Translation Required*
    4. Create new translation for plugin via right-click
    5. Click on the third button in the editor tab and choose the respective json file from your previously exported translation
    6. Click on "Done" and the translation should now be ported into the new format. (Recommended to save after this)
- Completely regenerated Vanilla Database
  - The old Database was exported via xTranslator and lacked a lot of strings, this means that it's now approx. double in size

### Other Fixes and Improvements

- Add Escape Shortcut to TranslatorDialog
- Add Open Button to Plugins' Contextmenu
  - This opens the plugin with the standard application configured in Windows
- Add error messagebox when API key is empty but DeepL is selected as Translator API
- Disable Terminal window for release builds
- Fix Context Menu when Rightclick is performed right outside of an Item
- Fix Downloads List in Downloads Tab
- Fix false Filtering of special Strings
  - Please report additional strings that are falsely filtered out from extraction (you can check the filtered strings in the log)
- Fix Open on Nexus Mods if translation has no ModID or FileID
- Fix edited string showing in Original column instead of translated column
- Fix Localisation of Translation Import
- Fix duplicate Translation Downloads
- Fix ImportDialog not cancelling when canceled
- Fix local Translation import
- Fix exception when INI file is missing while loading MO2 profiles
- Improve German Localisation
- Improve StringListDialog
- Improve Logger
- Improve CamelCase Check in Plugin Parser
- Improve Deep Scan
- Improve & optimize Translations from Database
- Mark Database Translations as Complete
- Optimize Merging of Translation and Original Strings (19k Strings now get merged in under 0.2s)
  - Switch to own implementation of StringMerger
- Display no version instead of "0" if a mod has no version in metadata
- Imported local Translations now have no version instead of "0"
- Minor Fixes and Improvements

# v1.0.5

- Improve precision of PluginParser String filter
- Build DSD Output only for installed Plugins instead of the whole Database
- Use FormIDs for all DIAL and INFO Records
- Add User Selection for MO2 Instance Profile to StartupDialog and User Settings
- Fix Nexus Mods scan of DSD Translations

# v1.0.4 (Hotfix)

- Fix missing Commandline Argument

# v1.0.3

- Add Commandline Arguments and "help" command
- Fix XXXX Subrecords in QUST and DIAL (fixes UnicodeDecodeError when parsing specific Plugins)
- Catch missing profiles Folder in MO2 Instance
- Minor Correction in Documentation
  - Removed note of previously unimplemented Features that are now implemented

# v1.0.2

- Fix Changelog in Updater
- Catch incomplete meta.ini of mod in MO2 instance

# v1.0.1

- Catch missing gameName in MO2 instance ini file
- Catch missing database index file
- Add error message when Vortex is running
- Add Vortex note to Documentation

# v1.0.0

- Initial Release
