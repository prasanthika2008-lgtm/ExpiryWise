def get_recommendation(name, days_left):
    name = name.lower()

    if days_left < 0:
        return "This product has expired. Please avoid consuming it."

    if days_left == 0:
        return "This product expires today. Please use it immediately."

    if days_left <= 2:
        return "Use this product very soon to avoid food waste."

    if days_left <= 5:
        return "This product is expiring soon. Consider using it in your next meal."

    if "milk" in name:
        return "You can use milk for tea, coffee, smoothies or cooking."

    if "bread" in name:
        return "You can use bread for sandwiches, toast or bread-based recipes."

    if "rice" in name:
        return "You can use rice for fried rice, lemon rice or other meals."

    if "vegetable" in name or "carrot" in name or "tomato" in name:
        return "Consider using this vegetable in your next meal."

    return "This product is still safe. Keep checking its expiry date."