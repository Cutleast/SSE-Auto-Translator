# Bundled dictionary notices

These `.aff` and `.dic` files are third-party resources. SSE-AT's project license
does not replace their individual terms. Their bytes and existing headers are
preserved. `dictionaries.json` identifies the exact bundled files by SHA-256.

| Files | Origin and attribution | Applicable terms |
| --- | --- | --- |
| `french.*` | Grammalecte / Olivier R.; bundled header: Classique 7.0 | MPL-2.0 |
| `german.*` | igerman98 / Björn Jacke; 20161207+frami20170109 | GPLv2 or GPLv3; both texts supplied |
| `italian.*` | LibreItalia; Turconi, Prina, Pescetti and Latini; 5.1.0 | GPL-3.0 |
| `japanese.*` | Gary, [hunspell_ja_JP](https://github.com/MrCorn0-0/hunspell_ja_JP/) | Upstream attribution notice; no SPDX license declared |
| `korean.*` | Changwoo Ryu / hunspell-dict-ko; bundled header: 0.7.92 | GPL-3.0-or-later |
| `polish.*` | sjp.pl; maintainer Marek Futrega | Upstream offers GPL, LGPL, MPL, Apache-2.0 and CC-SA alternatives; see original notice |
| `portuguese.*` | VERO / Raimundo Santos Moura and team; 3.2 | LGPL-3.0 and Mozilla Public License as stated upstream |
| `russian.*` | Alexander I. Lebedev; LibreOffice adaptations | Upstream BSD-style terms, including marking modifications |
| `spanish.*` | Santiago Bosio and contributors / LibreOffice | GPL-3.0-or-later, LGPL-3.0-or-later or MPL-1.1-or-later |

Full upstream notices are in `licenses/`; standard license texts are in
`../licenses/`. `licenses/upstream-notices.json` pins the source of each notice.
Some upstream companion notices describe newer dictionary versions; the versions
above and file hashes identify the files actually bundled here. No dictionary was
updated as part of adding these notices.

The Japanese upstream README asks: "Please indicate the origin when using."
This distribution credits Gary and retains the original notice in
`licenses/japanese.txt`. That notice is preserved as published and is not presented
as a GPL grant or a standardized software license.

The `.aff` and `.dic` files themselves are supplied in readable source form.
Upstream projects provide additional generators and development material; their
source locations are recorded in `dictionaries.json`.
