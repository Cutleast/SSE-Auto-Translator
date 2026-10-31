"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtWidgets import QApplication


class StringTypeNames:
    """
    Provides localized, human-readable names for plugin string types.
    """

    @staticmethod
    def get_record_name(signature: str) -> Optional[str]:
        """
        Gets the localized name of a record type.

        Args:
            signature (str): Record signature, for eg. "WEAP".

        Returns:
            Optional[str]: The localized name or None if the record type is unknown.
        """

        names: dict[str, str] = {
            "ACTI": QApplication.translate("StringTypeNames", "Activator"),
            "ALCH": QApplication.translate("StringTypeNames", "Potion/Food"),
            "AMMO": QApplication.translate("StringTypeNames", "Ammunition"),
            "APPA": QApplication.translate("StringTypeNames", "Apparatus"),
            "ARMO": QApplication.translate("StringTypeNames", "Armor"),
            "AVIF": QApplication.translate("StringTypeNames", "Skill/Actor value"),
            "BOOK": QApplication.translate("StringTypeNames", "Book"),
            "CELL": QApplication.translate("StringTypeNames", "Cell"),
            "CLAS": QApplication.translate("StringTypeNames", "Class"),
            "CONT": QApplication.translate("StringTypeNames", "Container"),
            "DIAL": QApplication.translate("StringTypeNames", "Dialogue topic"),
            "DOOR": QApplication.translate("StringTypeNames", "Door"),
            "ENCH": QApplication.translate("StringTypeNames", "Enchantment"),
            "EXPL": QApplication.translate("StringTypeNames", "Explosion"),
            "FACT": QApplication.translate("StringTypeNames", "Faction"),
            "FLOR": QApplication.translate("StringTypeNames", "Flora"),
            "FURN": QApplication.translate("StringTypeNames", "Furniture"),
            "GMST": QApplication.translate("StringTypeNames", "Game setting"),
            "HAZD": QApplication.translate("StringTypeNames", "Hazard"),
            "INFO": QApplication.translate("StringTypeNames", "Dialogue"),
            "INGR": QApplication.translate("StringTypeNames", "Ingredient"),
            "KEYM": QApplication.translate("StringTypeNames", "Key"),
            "LCTN": QApplication.translate("StringTypeNames", "Location"),
            "LIGH": QApplication.translate("StringTypeNames", "Light"),
            "LSCR": QApplication.translate("StringTypeNames", "Loading screen"),
            "MESG": QApplication.translate("StringTypeNames", "Message"),
            "MGEF": QApplication.translate("StringTypeNames", "Magic effect"),
            "MISC": QApplication.translate("StringTypeNames", "Misc item"),
            "NPC_": QApplication.translate("StringTypeNames", "NPC"),
            "PERK": QApplication.translate("StringTypeNames", "Perk"),
            "PROJ": QApplication.translate("StringTypeNames", "Projectile"),
            "QUST": QApplication.translate("StringTypeNames", "Quest"),
            "RACE": QApplication.translate("StringTypeNames", "Race"),
            "REFR": QApplication.translate("StringTypeNames", "Placed object"),
            "REGN": QApplication.translate("StringTypeNames", "Region"),
            "SCRL": QApplication.translate("StringTypeNames", "Scroll"),
            "SHOU": QApplication.translate("StringTypeNames", "Shout"),
            "SLGM": QApplication.translate("StringTypeNames", "Soul gem"),
            "SPEL": QApplication.translate("StringTypeNames", "Spell"),
            "TACT": QApplication.translate("StringTypeNames", "Talking activator"),
            "TREE": QApplication.translate("StringTypeNames", "Tree"),
            "WATR": QApplication.translate("StringTypeNames", "Water"),
            "WEAP": QApplication.translate("StringTypeNames", "Weapon"),
            "WOOP": QApplication.translate("StringTypeNames", "Word of power"),
            "WRLD": QApplication.translate("StringTypeNames", "Worldspace"),
        }

        return names.get(signature)

    @staticmethod
    def get_field_name(string_type: str) -> Optional[str]:
        """
        Gets the localized name of the field containing a string.

        Args:
            string_type (str): String type, for eg. "WEAP FULL".

        Returns:
            Optional[str]: The localized name or None if the field is unknown.
        """

        # Some subrecords have a different meaning depending on their record type.
        specific_names: dict[str, str] = {
            "BOOK CNAM": QApplication.translate("StringTypeNames", "Description"),
            "BOOK DESC": QApplication.translate("StringTypeNames", "Book text"),
            "GMST DATA": QApplication.translate("StringTypeNames", "Value"),
            "INFO NAM1": QApplication.translate("StringTypeNames", "Response"),
            "INFO RNAM": QApplication.translate("StringTypeNames", "Player prompt"),
            "MGEF DNAM": QApplication.translate("StringTypeNames", "Description"),
            "PERK EPF2": QApplication.translate("StringTypeNames", "Button text"),
            "PERK EPFD": QApplication.translate("StringTypeNames", "Entry text"),
            "QUST CNAM": QApplication.translate("StringTypeNames", "Journal entry"),
            "QUST NNAM": QApplication.translate("StringTypeNames", "Objective"),
            "WOOP TNAM": QApplication.translate("StringTypeNames", "Translation"),
        }
        names: dict[str, str] = {
            "DESC": QApplication.translate("StringTypeNames", "Description"),
            "FULL": QApplication.translate("StringTypeNames", "Name"),
            "ITXT": QApplication.translate("StringTypeNames", "Button text"),
            "RNAM": QApplication.translate("StringTypeNames", "Activation text"),
            "SHRT": QApplication.translate("StringTypeNames", "Short name"),
        }

        if string_type in specific_names:
            return specific_names[string_type]

        return names.get(string_type.split(" ")[-1])

    @staticmethod
    def get_string_kind(string_type: str) -> str:
        """
        Gets a localized description of a string type, for eg. "Weapon - Name".

        Args:
            string_type (str): String type, for eg. "WEAP FULL".

        Returns:
            str: The description with the raw record and field type as fallback.
        """

        record_signature, _, field_signature = string_type.partition(" ")
        record_name: str = (
            StringTypeNames.get_record_name(record_signature) or record_signature
        )
        field_name: str = StringTypeNames.get_field_name(string_type) or field_signature

        return f"{record_name} - {field_name}"
