"""
Test data loader — loads fixtures from test_data.json.
Can be used standalone (no AI needed) by any test script.
"""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent
DATA_FILE = FIXTURES_DIR / "test_data.json"


def load_test_data() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def get_users() -> dict:
    return load_test_data()["users"]


def get_products() -> dict:
    return load_test_data()["products"]


def get_recipes() -> dict:
    return load_test_data()["recipes"]


def get_scenarios() -> dict:
    return load_test_data()["scenarios"]


def get_user(key: str) -> dict:
    return get_users()[key]


def get_product(key: str) -> dict:
    return get_products()[key]


def get_recipe(key: str) -> dict:
    return get_recipes()[key]


def get_valid_products() -> list[tuple[str, dict]]:
    return [(k, v) for k, v in get_products().items() if not v.get("expectError")]


def get_invalid_products() -> list[tuple[str, dict]]:
    return [(k, v) for k, v in get_products().items() if v.get("expectError")]


def get_valid_recipes() -> list[tuple[str, dict]]:
    return [(k, v) for k, v in get_recipes().items() if not v.get("expectError")]


def get_invalid_recipes() -> list[tuple[str, dict]]:
    return [(k, v) for k, v in get_recipes().items() if v.get("expectError")]


if __name__ == "__main__":
    data = load_test_data()
    print(f"Users: {len(data['users'])} ({', '.join(data['users'].keys())})")
    print(f"Products: {len(data['products'])} ({len(get_valid_products())} valid, {len(get_invalid_products())} invalid)")
    print(f"Recipes: {len(data['recipes'])} ({len(get_valid_recipes())} valid, {len(get_invalid_recipes())} invalid)")
    print(f"Scenarios: {len(data['scenarios'])} ({', '.join(data['scenarios'].keys())})")
