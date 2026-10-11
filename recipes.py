"""Recipe ideas for items that need to be used soon (Phase 3).

Uses TheMealDB, a free public API that needs no key:
https://www.themealdb.com/api.php
"""
from functools import lru_cache

import requests

API_URL = "https://www.themealdb.com/api/json/v1/1/filter.php"

# Product-name keyword -> ingredient name that TheMealDB understands
INGREDIENT_MAP = {
    "chicken": "chicken",
    "fish": "salmon",
    "egg": "eggs",
    "milk": "milk",
    "curd": "yogurt",
    "yogurt": "yogurt",
    "paneer": "paneer",
    "bread": "bread",
    "rice": "rice",
    "tomato": "tomatoes",
    "carrot": "carrots",
    "banana": "bananas",
    "spinach": "spinach",
    "potato": "potatoes",
}


def main_ingredient(product_name):
    """Return the ingredient to search for, or None if we don't recognise the product."""
    name = (product_name or "").lower()
    for keyword, ingredient in INGREDIENT_MAP.items():
        if keyword in name:
            return ingredient
    return None


@lru_cache(maxsize=128)
def _fetch(ingredient):
    response = requests.get(API_URL, params={"i": ingredient}, timeout=6,
                            headers={"User-Agent": "ExpiryWise/0.3 (student project)"})
    return response.json().get("meals") or []


def get_recipe_ideas(product_name, limit=3):
    """Return up to `limit` recipes as [{'name', 'url'}]. Never raises."""
    ingredient = main_ingredient(product_name)
    if ingredient is None:
        return []
    try:
        meals = _fetch(ingredient)
    except (requests.RequestException, ValueError):
        return []
    return [
        {"name": m["strMeal"], "url": f"https://www.themealdb.com/meal/{m['idMeal']}"}
        for m in meals[:limit]
    ]
