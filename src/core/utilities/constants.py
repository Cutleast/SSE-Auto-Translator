"""
Copyright (c) Cutleast
"""

# Vanilla Plugins
BASE_GAME_PLUGINS = [
    "skyrim.esm",
    "update.esm",
    "dawnguard.esm",
    "hearthfires.esm",
    "dragonborn.esm",
    "skyrimvr.esm",
]
"""
A list of all base game plugins, excluding Creation Club.
"""

AE_CC_PLUGINS = [
    "ccbgssse002-exoticarrows.esl",
    "ccbgssse003-zombies.esl",
    "ccbgssse004-ruinsedge.esl",
    "ccbgssse005-goldbrand.esl",
    "ccbgssse006-stendarshammer.esl",
    "ccbgssse007-chrysamere.esl",
    "ccbgssse008-wraithguard.esl",
    "ccbgssse010-petdwarvenarmoredmudcrab.esl",
    "ccbgssse011-hrsarmrelvn.esl",
    "ccbgssse012-hrsarmrstl.esl",
    "ccbgssse013-dawnfang.esl",
    "ccbgssse014-spellpack01.esl",
    "ccbgssse016-umbra.esm",
    "ccbgssse018-shadowrend.esl",
    "ccbgssse019-staffofsheogorath.esl",
    "ccbgssse020-graycowl.esl",
    "ccbgssse021-lordsmail.esl",
    "ccbgssse025-advdsgs.esm",
    "ccbgssse031-advcyrus.esm",
    "ccbgssse034-mntuni.esl",
    "ccbgssse035-petnhound.esl",
    "ccbgssse036-petbwolf.esl",
    "ccbgssse037-curios.esl",
    "ccbgssse038-bowofshadows.esl",
    "ccbgssse040-advobgobs.esl",
    "ccbgssse041-netchleather.esl",
    "ccbgssse043-crosselv.esl",
    "ccbgssse045-hasedoki.esl",
    "ccbgssse050-ba_daedric.esl",
    "ccbgssse051-ba_daedricmail.esl",
    "ccbgssse052-ba_iron.esl",
    "ccbgssse053-ba_leather.esl",
    "ccbgssse054-ba_orcish.esl",
    "ccbgssse055-ba_orcishscaled.esl",
    "ccbgssse056-ba_silver.esl",
    "ccbgssse057-ba_stalhrim.esl",
    "ccbgssse058-ba_steel.esl",
    "ccbgssse059-ba_dragonplate.esl",
    "ccbgssse060-ba_dragonscale.esl",
    "ccbgssse061-ba_dwarven.esl",
    "ccbgssse062-ba_dwarvenmail.esl",
    "ccbgssse063-ba_ebony.esl",
    "ccbgssse064-ba_elven.esl",
    "ccbgssse066-staves.esl",
    "ccbgssse067-daedinv.esm",
    "ccbgssse068-bloodfall.esl",
    "ccbgssse069-contest.esl",
    "cccbhsse001-gaunt.esl",
    "ccedhsse001-norjewel.esl",
    "ccedhsse002-splkntset.esl",
    "ccedhsse003-redguard.esl",
    "cceejsse001-hstead.esm",
    "cceejsse002-tower.esl",
    "cceejsse003-hollow.esl",
    "cceejsse004-hall.esl",
    "cceejsse005-cave.esm",
    "ccffbsse001-imperialdragon.esl",
    "ccffbsse002-crossbowpack.esl",
    "ccfsvsse001-backpacks.esl",
    "cckrtsse001_altar.esl",
    "ccmtysse001-knightsofthenine.esl",
    "ccmtysse002-ve.esl",
    "ccpewsse002-armsofchaos.esl",
    "ccqdrsse001-survivalmode.esl",
    "ccqdrsse002-firewood.esl",
    "ccrmssse001-necrohouse.esl",
    "cctwbsse001-puzzledungeon.esm",
    "ccvsvsse001-winter.esl",
    "ccvsvsse002-pets.esl",
    "ccvsvsse003-necroarts.esl",
    "ccvsvsse004-beafarmer.esl",
    "ccafdsse001-dwesanctuary.esm",
    "ccasvsse001-almsivi.esm",
    "ccbgssse001-fish.esm",
]
"""
A list of all Creation Club plugins that came with the AE update and upgrade.
"""

DSD_FILE_PATTERN: str = "**/SKSE/Plugins/DynamicStringDistributor/*/*.json"
"""
The glob pattern for DSD files.
"""

# Supported languages
SUPPORTED_LANGS: list[tuple[str, str]] = [
    ("chinese", "zh_CN"),
    ("french", "fr_FR"),
    ("german", "de_DE"),
    ("italian", "it_IT"),
    ("japanese", "jp_JP"),
    ("korean", "ko_KR"),
    ("polish", "pl_PL"),
    ("portuguese", "pt_BR"),
    ("russian", "ru_RU"),
    ("spanish", "es_ES"),
]
"""
A list of supported languages.
"""