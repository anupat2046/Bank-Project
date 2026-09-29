"""Audited crosswalk: BOT English spellings -> DOPA two-digit province codes.

Never fuzzy-join an unknown name. New spellings fail ingestion until reviewed.
"""
from __future__ import annotations

import re

BOT_TO_CODE = {
    "Bangkok": 10, "Samutprakan": 11, "Nonthaburi": 12, "Pathumthani": 13,
    "Ayuthaya": 14, "Angthong": 15, "Lopburi": 16, "Singburi": 17,
    "Chainat": 18, "Saraburi": 19, "Chonburi": 20, "Rayong": 21,
    "Chanthaburi": 22, "Trad": 23, "Chachoengsao": 24, "Prachinburi": 25,
    "Nakhonnayok": 26, "Sakaew": 27, "Nakhonratchasima": 30,
    "Buriram": 31, "Surin": 32, "Srisaket": 33, "Ubonratchathani": 34,
    "Yasothon": 35, "Chaiyaphum": 36, "Amnatcharoen": 37,
    "Bueng Kan": 38, "Nongbuarampu": 39, "Khonkaen": 40,
    "Udonthani": 41, "Loei": 42, "Nongkhai": 43, "Mahasarakam": 44,
    "Roiet": 45, "Kalasin": 46, "Sakonnakhon": 47,
    "Nakhonphanom": 48, "Mukdahan": 49, "Chiengmai": 50,
    "Lamphun": 51, "Lampang": 52, "Uttaradit": 53, "Phrea": 54,
    "Nan": 55, "Phayao": 56, "Chiengrai": 57, "Maehongson": 58,
    "Nakhonsawan": 60, "Uthaithani": 61, "Kamphaengphet": 62,
    "Tak": 63, "Sukhothai": 64, "Phitsanulok": 65,
    "Phichit": 66, "Phetchabun": 67, "Ratchaburi": 70,
    "Kanchanaburi": 71, "Suphanburi": 72, "Nakhonpathom": 73,
    "Samutsakhon": 74, "Samutsongkhram": 75, "Phetchaburi": 76,
    "Prachuapkhirikhun": 77, "Nakhonsithammarat": 80,
    "Krabi": 81, "Phangnga": 82, "Phuket": 83,
    "Suratthani": 84, "Ranong": 85, "Chumphon": 86,
    "Songkhla": 90, "Satul": 91, "Trang": 92,
    "Phatthalung": 93, "Pattani": 94, "Yala": 95,
    "Narathiwat": 96,
}

assert len(BOT_TO_CODE) == 77 and len(set(BOT_TO_CODE.values())) == 77

NESDC_ALIASES = {
    "BANGKOK METROPOLIS": "Bangkok", "PHRA NAKHON SI AYUTTHAYA": "Ayuthaya",
    "AYUTTHAYA": "Ayuthaya", "BURIRAM": "Buriram", "SISAKET": "Srisaket",
    "SI SA KET": "Srisaket", "BUENGKAN": "Bueng Kan",
    "NONG BUA LAMPHU": "Nongbuarampu", "AMNAT CHAROEN": "Amnatcharoen",
    "MAHA SARAKHAM": "Mahasarakam", "ROI ET": "Roiet",
    "CHIANG MAI": "Chiengmai", "CHIANG RAI": "Chiengrai",
    "PHRAE": "Phrea", "MAE HONG SON": "Maehongson",
    "PRACHUAP KHIRI KHAN": "Prachuapkhirikhun",
    "NAKHON SI THAMMARAT": "Nakhonsithammarat", "SATUN": "Satul",
    "TRAT": "Trad", "SA KAEO": "Sakaew",
    "NONGBUA LAMPHU": "Nongbuarampu", "AMNAT CHAREON": "Amnatcharoen",
    "KAM PHAENG PHET": "Kamphaengphet", "PHACHUAP KHIRI KHAN": "Prachuapkhirikhun",
    "PHRA NAKHON SRI AYUTHAYA": "Ayuthaya", "PHANGNGA": "Phangnga",
}


def province_code_from_nesdc(name: str) -> int:
    clean = re.sub(r"^\d{4}\s*[- ]\s*", "", name.upper()).strip()
    canonical = NESDC_ALIASES.get(clean, clean)
    compact = re.sub(r"[^A-Z]", "", canonical.upper())
    matches = [code for bot, code in BOT_TO_CODE.items()
               if re.sub(r"[^A-Z]", "", bot.upper()) == compact]
    if len(matches) != 1:
        raise ValueError(f"Unmapped NESDC province: {name!r}")
    return matches[0]
