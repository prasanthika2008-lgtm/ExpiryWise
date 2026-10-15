"""
recommendation.py
Rule-based recommendations, now category-aware (Phase 2).

Provides:
  get_status()          label a product as Safe / Expiring Soon / Expired
  get_recommendation()  a short "what to do with it" message

No AI or network is used. The advice comes from the keyword tables below.
"""

# Ideas shown for items that are still safe, matched on product name keywords.
# If the product name contains the key (for example "full cream milk"
# contains "milk"), the idea is added to the message.
USE_IDEAS = {
    "milk": "Use it for tea, coffee, smoothies, curd or payasam.",
    "curd": "Make buttermilk, raita or a lassi.",
    "yogurt": "Blend into a smoothie or use it as a marinade.",
    "bread": "Make sandwiches, toast, or bread upma / pudding.",
    "rice": "Cook lemon rice, fried rice or curd rice.",
    "tomato": "Cook it into rasam, chutney or a tomato sauce.",
    "carrot": "Make a stir-fry, halwa or add it to soups.",
    "banana": "Blend into a shake or bake banana bread.",
    "egg": "Boil, scramble or make an omelette.",
    "paneer": "Make paneer curry, bhurji or tikka.",
    "chicken": "Cook it today or freeze it in portions.",
    "fish": "Cook it today or freeze it in portions.",
    "spinach": "Make dal palak, a smoothie or a stir-fry.",
    "potato": "Make a curry, mash or fries.",
    "vegetable": "Use it in a mixed-vegetable curry, soup or stir-fry.",
}

# General storage advice per category, used when no name keyword matches.
CATEGORY_TIPS = {
    "Dairy": "Dairy spoils quickly once opened. Keep it refrigerated.",
    "Meat": "Freeze meat if you cannot cook it within a day or two.",
    "Fruits": "Ripe fruit can be blended, stewed or frozen.",
    "Vegetables": "Cooked vegetables can be frozen for later.",
    "Bakery": "Slices of bread can be frozen to extend their life.",
    "Medicine": "Do not use expired medicine. Dispose of it safely.",
    "Packaged": "Check the pack for 'consume within X days of opening'.",
}


def get_status(days_left, soon_threshold=5):
    """Return 'Expired', 'Expiring Soon' or 'Safe'.

    Args:
        days_left: Days until expiry. Negative means already expired.
        soon_threshold: A product is "Expiring Soon" when this many days
            or fewer remain (default 5).

    Returns:
        str: One of "Expired", "Expiring Soon" or "Safe".
    """
    if days_left < 0:
        return "Expired"
    if days_left <= soon_threshold:
        return "Expiring Soon"
    return "Safe"


def get_recommendation(name, days_left, category=None):
    """Return a short message telling the user what to do with a product.

    The message depends on how many days are left:
      expired      -> warning not to use it (stronger wording for Medicine)
      today        -> use immediately
      1 to 2 days  -> use very soon
      3 to 5 days  -> plan it into the next meal
      more than 5  -> a usage idea, else a category tip, else a generic note
    A usage idea from USE_IDEAS is appended when the name matches a keyword.

    Args:
        name: Product name (may be None or empty).
        days_left: Days until expiry. Negative means already expired.
        category: Product category, for example "Dairy" or "Medicine".

    Returns:
        str: The recommendation text.
    """
    name = (name or "").lower()

    # Expired items: never suggest eating or using them.
    if days_left < 0:
        if category == "Medicine":
            return "This medicine has expired. Do not use it; dispose of it safely."
        return "This product has expired. Please avoid consuming it."

    # Find the first keyword in USE_IDEAS that appears in the product name.
    idea = next((tip for key, tip in USE_IDEAS.items() if key in name), None)

    # Urgent items: urgency message first, then the idea (if there is one).
    if days_left == 0:
        return "Expires today. Use it immediately." + (f" {idea}" if idea else "")
    if days_left <= 2:
        return "Use this very soon to avoid waste." + (f" {idea}" if idea else "")
    if days_left <= 5:
        return "Expiring soon, plan it into your next meal." + (f" {idea}" if idea else "")

    # Safe items: best available advice, from most to least specific.
    if idea:
        return idea
    if category in CATEGORY_TIPS:
        return CATEGORY_TIPS[category]
    return "This product is still safe. Keep checking its expiry date."