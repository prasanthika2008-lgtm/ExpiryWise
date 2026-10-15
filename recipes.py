"""
recipes.py
Recipe ideas for items that need to be used soon (Phase 2).

Uses TheMealDB, a free public API that needs no key:
https://www.themealdb.com/api.php

Flow:
  product name -> main_ingredient() -> _fetch() (API call) -> get_recipe_ideas()

get_recipe_ideas() never raises an error. If the product is not recognised
or the internet is down, it returns an empty list and the app keeps working.
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
    """Return the ingredient to search for, or None if we don't recognise the product.

    Args:
        product_name: Product name such as "Amul Fresh Milk" (may be None).

    Returns:
        str or None: The ingredient name TheMealDB understands, for example
        "milk", or None if no keyword in INGREDIENT_MAP matches.
    """
    name = (product_name or "").lower()
    for keyword, ingredient in INGREDIENT_MAP.items():
        if keyword in name:
            return ingredient
    return None


# lru_cache remembers the last 128 results, so asking for the same
# ingredient again does not call the API a second time.
@lru_cache(maxsize=128)
def _fetch(ingredient):
    """Call TheMealDB and return the list of meals for one ingredient.

    Raises:
        requests.RequestException: If the network call fails.
        ValueError: If the response is not valid JSON.
        (get_recipe_ideas() catches both.)

    Returns:
        list[dict]: Meals from the API, or an empty list if there are none.
    """
    response = requests.get(API_URL, params={"i": ingredient}, timeout=6,
                            headers={"User-Agent": "ExpiryWise/0.3 (student project)"})
    return response.json().get("meals") or []


def get_recipe_ideas(product_name, limit=3):
    """Return up to `limit` recipes as [{'name', 'url'}]. Never raises.

    Args:
        product_name: Product name such as "Chicken breast".
        limit: Maximum number of recipes to return (default 3).

    Returns:
        list[dict]: Each item has "name" and "url". The list is empty when the
        product is not recognised or the recipe service cannot be reached.
    """
    ingredient = main_ingredient(product_name)
    if ingredient is None:
        return []
    try:
        meals = _fetch(ingredient)
    except (requests.RequestException, ValueError):
        # No internet, timeout, or a bad response: show no recipes, don't crash.
        return []
    return [
        {"name": m["strMeal"], "url": f"https://www.themealdb.com/meal/{m['idMeal']}"}
        for m in meals[:limit]
    ]