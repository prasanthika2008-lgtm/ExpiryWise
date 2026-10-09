"""Rule-based recommendations, now category-aware (Phase 2)."""

# Ideas shown for items that are still safe, matched on product name keywords
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
    """Return 'Expired', 'Expiring Soon' or 'Safe'."""
    if days_left < 0:
        return "Expired"
    if days_left <= soon_threshold:
        return "Expiring Soon"
    return "Safe"


def get_recommendation(name, days_left, category=None):
    name = (name or "").lower()

    if days_left < 0:
        if category == "Medicine":
            return "This medicine has expired. Do not use it; dispose of it safely."
        return "This product has expired. Please avoid consuming it."

    idea = next((tip for key, tip in USE_IDEAS.items() if key in name), None)

    if days_left == 0:
        return "Expires today. Use it immediately." + (f" {idea}" if idea else "")
    if days_left <= 2:
        return "Use this very soon to avoid waste." + (f" {idea}" if idea else "")
    if days_left <= 5:
        return "Expiring soon, plan it into your next meal." + (f" {idea}" if idea else "")

    if idea:
        return idea
    if category in CATEGORY_TIPS:
        return CATEGORY_TIPS[category]
    return "This product is still safe. Keep checking its expiry date."
