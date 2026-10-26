# Licensing and corresponding source

Copyright (c) Cutleast and contributors.

SSE Auto Translator's first-party code is licensed under the GNU General Public
License, version 3. See `LICENSE` for the complete terms. This replaces the previous
CC BY-NC-ND licensing for the first-party code in this revision.

Third-party code, resources, submodules and test fixtures retain their own terms.
In particular, the project license does not relicense:

- Hunspell dictionaries: see `res/hunspell/README.md` and its accompanying notices.
- 7-Zip: see `res/7-zip/7z_License.txt`.
- `core-lib`, `core-res`, `mod-manager-lib` and Python/native dependencies.
- Third-party mod files under `tests/data`; their authors are credited in
  `README.md`. These fixtures are excluded from the release source archive.
- Third-party logos and `TaskbarLib.tlb`; preserve their upstream provenance and
  applicable redistribution terms.

## Release contents

The build includes this notice, the GPL text, `res/licenses`, dictionary notices,
and a `licenses` directory containing license files found in the installed runtime
dependency distributions. `licenses/dependencies.json` records the actual package
versions, their metadata, and source archive references from `uv.lock`. The build
fails if a required package does not match its locked version.

`source/SSE-AT.zip` contains the application's source, build scripts, lockfile and
checked-out submodule sources from the build checkout. It includes local changes;
`source/revisions.json` records the Git revisions and whether that checkout was
modified. Generated application resources and third-party mod test fixtures are
excluded. To build, extract the source archive, install Python 3.14 and uv, run
`uv sync --locked`, then run `build.bat` from the extracted project root.

Publish the matching source material together with every binary release. Source
links in the dependency inventory help identify upstream versions; links alone are
not a substitute for providing corresponding source where a license requires it.
Before publishing, obtain and provide the matching sources and build changes for
bundled native libraries, including Qt/PySide, 7-Zip and libraries embedded in wheels.
The inventory of Python package notices does not certify those native components.

## Qt, PySide and other LGPL components

Qt and PySide are third-party software distributed under their applicable
GPL/LGPL terms. Copies of GPL and LGPL texts are included in `res/licenses`.
QtWebEngine additionally contains Chromium and other third-party components:
preserve their version-specific notices when distributing the embedded browser.
The build records the matching Qt documentation and source locations in the
dependency inventory. The embedded browser's `chrome://qt` page also exposes its
third-party acknowledgements.

The standalone distribution uses separate shared libraries. Recipients may replace
LGPL libraries with modified, interface-compatible versions and debug those
modifications, including by reverse engineering as permitted by the applicable
license. No first-party license term removes these rights. Keep the shared-library
layout and required plugins when repackaging the application.
