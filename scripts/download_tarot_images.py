#!/usr/bin/env python3
"""Download Rider-Waite tarot card images from sacred-texts.com"""

import urllib.request
import time
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"
IMAGES_DIR = KB_DIR / "images"

# sacred-texts.com URL pattern for Rider-Waite images
# Major Arcana: ar000.gif (Fool) to ar021.gif (World)
# Minor Arcana follow a pattern by suit and number

# Card ID to sacred-texts filename mapping
MAJOR_ARCANA_MAP = {
    "major_00_fool": "ar000",
    "major_01_magician": "ar001",
    "major_02_high_priestess": "ar002",
    "major_03_empress": "ar003",
    "major_04_emperor": "ar004",
    "major_05_hierophant": "ar005",
    "major_06_lovers": "ar006",
    "major_07_chariot": "ar007",
    "major_08_strength": "ar011",  # Note: Strength is XI in RWS
    "major_09_hermit": "ar009",
    "major_10_wheel_of_fortune": "ar010",
    "major_11_justice": "ar008",  # Note: Justice is VIII in RWS
    "major_12_hanged_man": "ar012",
    "major_13_death": "ar013",
    "major_14_temperance": "ar014",
    "major_15_devil": "ar015",
    "major_16_tower": "ar016",
    "major_17_star": "ar017",
    "major_18_moon": "ar018",
    "major_19_sun": "ar019",
    "major_20_judgement": "ar020",
    "major_21_world": "ar021",
}

# Minor Arcana mapping
# Wands: 1-14, Cups: 101-114, Swords: 201-214, Pentacles: 301-314
MINOR_ARCANA_MAP = {}

# Wands (suits start at different offsets)
for i in range(1, 15):
    num = i if i <= 10 else i + 3  # Page=11, Knight=12, Queen=13, King=14
    suit_id = 100
    file_num = suit_id + i
    card_names = {
        1: "ace", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "page", 12: "knight", 13: "queen", 14: "king"
    }
    name = card_names.get(i, f"_{i}")
    MINOR_ARCANA_MAP[f"minor_wands_{i-1:02d}_{name}"] = f"ar{file_num:03d}"

# Cups
for i in range(1, 15):
    suit_id = 110
    file_num = suit_id + i - 10
    card_names = {
        1: "ace", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "page", 12: "knight", 13: "queen", 14: "king"
    }
    name = card_names.get(i, f"_{i}")
    MINOR_ARCANA_MAP[f"minor_cups_{i-1:02d}_{name}"] = f"ar{file_num:03d}"

# Swords
for i in range(1, 15):
    suit_id = 120
    file_num = suit_id + i - 10
    card_names = {
        1: "ace", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "page", 12: "knight", 13: "queen", 14: "king"
    }
    name = card_names.get(i, f"_{i}")
    MINOR_ARCANA_MAP[f"minor_swords_{i-1:02d}_{name}"] = f"ar{file_num:03d}"

# Pentacles
for i in range(1, 15):
    suit_id = 130
    file_num = suit_id + i - 10
    card_names = {
        1: "ace", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "page", 12: "knight", 13: "queen", 14: "king"
    }
    name = card_names.get(i, f"_{i}")
    MINOR_ARCANA_MAP[f"minor_pentacles_{i-1:02d}_{name}"] = f"ar{file_num:03d}"


def download_images():
    IMAGES_DIR.mkdir(exist_ok=True)
    
    all_cards = {**MAJOR_ARCANA_MAP, **MINOR_ARCANA_MAP}
    base_url = "https://www.sacred-texts.com/tarot/pkt/img/"
    
    downloaded = 0
    failed = 0
    
    for card_id, filename in all_cards.items():
        output_path = IMAGES_DIR / f"{card_id}.gif"
        
        if output_path.exists():
            print(f"  Skip (exists): {card_id}")
            downloaded += 1
            continue
        
        url = f"{base_url}{filename}.gif"
        try:
            print(f"  Downloading: {card_id} from {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(output_path, "wb") as f:
                    f.write(response.read())
            downloaded += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  Failed: {card_id} - {e}")
            failed += 1
    
    print(f"\nDone: {downloaded} downloaded, {failed} failed")
    return downloaded


if __name__ == "__main__":
    print("Downloading Rider-Waite tarot images...")
    download_images()
