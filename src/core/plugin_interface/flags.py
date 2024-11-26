"""
Copyright (c) Cutleast
"""

from .datatypes import Flags


class RecordFlags(Flags):
    Master = 0x1
    DeletedGroup = 0x10
    Deleted = 0x20
    Constant = HiddenFromLocalMap = 0x40
    Localized = 0x80
    MustUpdateAnims = Inaccessible = 0x100
    LightMaster = HiddenFromLocalMap2 = MotionBlurCastsShadows = 0x200
    PersistentReference = QuestItem = 0x400
    InitiallyDisabled = 0x800
    Ignored = 0x1000
    VisibleWhenDistant = 0x8000
    Dangerous = 0x20000
    Compressed = 0x40000
    CantWait = 0x80000
    IsMarker = 0x100000
    NoAIAcquire = 0x2000000
    NavMeshGenFilter = 0x4000000
    NavMeshGenBoundingBox = 0x8000000
    ReflectedByAutoWater = 0x10000000
    DontHavokSettle = 0x20000000
    NavMeshGenGround = NoRespawn = 0x40000000
    MultiBound = 0x80000000
