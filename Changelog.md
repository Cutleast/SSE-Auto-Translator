# v2.1.10 (Hotfix)

- Fix Mod Manager (and non-premium Nexus Mods) downloads

# v2.1.9

- Add Turkish to supported languages (no Vanilla database, though as there is no official localisation of the game)
- Fix random CTDs when downloading translations
- Fix crash when launched via Wine (Linux)
- Fix browser not opening when clicking on links in SSE-AT for some users

# v2.1.8

- Apply default values to translator config when loading user config
- Improve error handling when requesting mod details
- Catch exceptions when processing meta.ini files
- Add support for Indonesian
- Strip quotation marks from INI file values

# v2.1.7

- Fix online scan for Chinese translations because their named "Mandarin" on Nexus Mods now
- Improve Chinese localisation for TranslationInstalled plugin status (thanks to [GF-Huang](https://github.com/Cutleast/SSE-Auto-Translator/commits?author=GF-Huang)!)

# v2.1.6

- Fix loading of MO2 mods where "file_id" is empty in meta.ini

# v2.1.5

- Fix UnicodeDecodeError when requesting mod translations
- Catch and log potential errors when loading a translation from a JSON file
- Fix UnicodeDecodeError when parsing certain plugins with QUST XXXX fields (eg. "Inns Can Be Closed.esp")

# v2.1.4

- Catch potential API errors when scanning for translations
- Fix NoneType AttributeError that's caused by a plugin in a separator (Eldergleam)
- Increase resiliency for malformed DSD translations

# v2.1.3

- Fix NotADirectoryError when downloading translations with illegal characters (for eg. ":")

# v2.1.2

- Fix "%BASE_DIR%" not being fully resolved when loading some MO2 instances
- Fix dev environment paths appearing in tracebacks

# v2.1.1

#### If not already done for v2.0.1: It is heavily recommended to delete everything but the "data" folder from the "SSE-AT" folder before updating! Your User Data is not affected. See v2.0.1 Changelog for more information.

- Fix rare IndexError when sorting TranslationDownloads

# v2.1.0

#### If not already done for v2.0.1: It is heavily recommended to delete everything but the "data" folder from the "SSE-AT" folder before updating! Your User Data is not affected. See v2.0.1 Changelog for more information.

### Highlights

- Add "Date" and "Size" columns to "Translations" list
- Add experimental "Apply Translation" feature to context menu of Plugin translations
  - This writes the translated strings to a copy of the original Plugin (similar to xTranslator's "Finalize ESP/ESM")
- Add runtime cache for Plugin Strings (optimizes access times)
- Add actions for current mod selection
- Add drag'n drop import for Translations
  - To import one or more Translations, just drag them in the Translations panel
- Add more "Copy" buttons to StringListDialog
- Add "Do not show again" button to Translator APIs
- Add setting for persistent Downloads path
  - This defaults to the temp folder which gets wiped after exit
  - Changing this to a separate folder prevents it from getting wiped
  - This can be set to an existing Downloads folder
- Add Browser Documentation button to StartupDialog
- Add option to edit all Plugins of a Translation at once
  - You can now click on the Translation item itself in the TranslationEditor and it will show all Strings from all Plugins of that Translation
- Add author blacklist to UserSettings
- Add Russian localisation (thanks to [xsSplater](https://github.com/xsSplater)!)

### Other Fixes and Improvements

- Database translations for same mods are now merged
- Set FE FormID Prefix for Records first-defined in light-flagged Plugins
- Hide Plugin items without visible Strings in StringListDialog
- Change default Provider Setting for French
- Disable inclusion of Papyrus Scripts by default
- Replace improvised Plugin Parser by new Plugin Interface
- Decrease default font size in UI to increase number of visible items on screen
  - It now matches your system font size
- Delete temporary text file after archive extraction with 7-zip commandline
- Show error messageboxes over active modal widget
- Copy non-Plugin files when manually creating a new Translation
- Import only interface translations for desired language
- Improve layouts in UserSettings and StartupDialog by adding group boxes
- Improve Scrollbar visibilty
- Optimize search bar behaviour for large (>1k) modlists and databases
- Optimize mass API translations
- Optimize import of non-Plugin files
- Optimize scrolling when there are a lot of items (Modlist, Translations, StringListDialog, TranslationEditor)
- Fix import of loose non-Plugin files
- Fix non-Premium "Download" buttons
- Fix FileExistsError when building Output Mod
- Fix provider preference setting getting resetted at each start

# v2.0.1

#### Due to a change in the way SSE-AT is built, to deal with AV false positives, it is heavily recommended to delete everything but the "data" folder from the "SSE-AT" folder before updating! Your User Data is not affected.

- Fix Manual API Setup in StartupDialog
- Fix "{USERDATA}" in Vortex's staging folder path
- Attempt to fix AV false detections
- Fix PT-BR when translating with Google
- Fix masterlist not loading

# v2.0.0

### Highlights

- Support for la Confrérie des Traducteurs (thanks to [Oaristys](https://next.nexusmods.com/profile/Oaristys) and [Aldranor](https://github.com/Aldranor) for their help)
- **Limited** support for non-Plugin files like interface translations, Papyrus scripts, textures and sounds
  - The files are not scanned, cannot be edited from within SSE-AT and are just extracted and copied from downloaded translations
- Caching System
  - Plugin strings are now cached to avoid multiple parsings
  - Plugin states are saved when exiting SSE-AT
  - Web and API requests are saved for 12 hours
  - Add a "Clear Cache" button to App Settings
- Support for third-party masterlists
  - Please contact us via our Discord server if you want to maintain a masterlist for your language or have questions
- Overhaul non-Premium downloads from Nexus Mods (see Documentation for more info)
  - Add toast notification for downloads started from browser

### Other Fixes and Improvements

- Add warning to settings if path to output mod is not empty
- Add setting for path of temp folder
- Fix obsolete processing of duplicate plugins
- Fix duplicate downloads in queue
- Improve DownloadListDialog
- Improve handling of failed downloads
  - The actual error is now displayed when hovering over the downloads
- Display progress of LoadingDialog in taskbar
- Reduce flickering of LoadingDialog
- Optimize startup time by switching to new database format instead of JSON files
- Save database everytime a translation is added or deleted
- Update chinese translation (thanks to [grox1313](https://github.com/grox1313))
- Replace pointless RadioButton in Modlist String Search by CheckBox
- Fix archive extraction when there is a large number of plugins to extract
- Fix export of multiple translations
  - It is now possible to select multiple translations in the "Translations" tab and export them all at once
- Fix and improve import of multiple variants of the same plugin in a translation
- Fix download thread not stopping when exiting SSE-AT
- Fix "Check for Updates" button in "Help" menu
- Fix Chinese and Portuguese in Google Translator and DeepL APIs
- Fix ValueError for incomplete meta.ini files in MO2 instances

# v1.2.1 (Hotfix)

- Fix missing 7-zip files that are required for extraction of archives

# v1.2.0

### New Features

- Translation Editor
  - Add Shortcuts for finalizing and switching to next/prev string
  - Same untranslated Strings now get auto-translated upon finalization
  - Add optional Spell Checking Feature to Translator Dialog
  - Add Reset Button with Shortcut to Translator Dialog
  - Add FormID Label to Translator Dialog
- Improve Search Bars and add Case Sensitivity Toggle
- Add Delete Shortcut to "Translations" Tab
- Add new Settings for toggling Spell Checking Feature and setting DSD Output path
- Add nesting feature to StringListDialog
  - Strings from multiple Plugins now get grouped together
  - Add "Copy Plugin Name" option to contextmenu
- Add String Search Features to the entire modlist and the database
- Add Bar Graph to MainPage and TranslationEditor displaying Status Ratios

### Fixes and Improvements

- Set "Yes" as Standard Button in most messageboxes
- Fix API Key not applying when starting with invalid API Key
- Limit supported languages to relevant ones
  - This includes all languages supported by the game + Korean and Portuguese
- Fix issue with Vortex database that came from non-ASCII characters in the database's path
- Translation Editor: fix tab close button changing selected tab on hover
- Startup Dialog: fix validation on modinstance selection
- Catch all requests exceptions in Updater
- Strip Mod Versions of obsolete ".0" for Vortex modlists
- Add additional logging to Vortex
- Display App Version in Titlebars
- Add "no restart required" note to some settings
- Fix Vortex Staging Folder Path
- Replace default clear buttons in input fields by custom ones
- Remove "[Experimental]" note from Deep Scan
- Fix unchanged strings marked as "TranslationIncomplete" when using Search and Replace
- Switch completely to 7-zip commandline
- Fix Translation Import from Archives
- Fix reloading of translations ignoring active filter in "Translations" Tab

# v1.1.1

##### If not already done for the last update: Please wipe your SSE-AT folder before updating. See v1.1 below for more information.

### New Features

- Advanced Users only: Added a button to Plugin's Contextmenu to view the Structure of Plugins
  - This can take a while and block the rest of the app for large and complex Plugins

### Fixes and Improvements

- Fix potential NoneType Error when trimming Strings
- Fix error when debugging Parser
- Fix extraction of missing REGN RDMP strings
- Catch rare decoding errors due to invalid encoded strings in some plugins
- Fix edited strings appearing in wrong column
  - this time when using *Search and Replace* or *API Translation*
- Database is now saved more often to reduce potential of lost translations due to crashes
- Minor improvement to Plugin's Contextmenu
- Fix crashes caused by log spamming
- First two digits of FormIDs are now ignored when merging translation and original or translating with the database
  - This previously lead to the issue that strings could not be merged for an outdated translation if the original has different masters
- Added failsafe for corrupt archives instead of getting stuck

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
