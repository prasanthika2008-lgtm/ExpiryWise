def get_recommendation(name, days_left):

    name = name.lower()

    if days_left < 0:
        return f"{name.title()} has already expired. Please do not consume it."

    elif days_left == 0:
        return f"{name.title()} expires today. Use it immediately if it is still safe."

    elif days_left <= 2:
        return f"{name.title()} expires very soon. Try to use it today or tomorrow."

    elif days_left <= 5:
        return f"{name.title()} is expiring soon. Plan a meal or use it before the expiry date."

    elif name == "milk":
        return "Milk is still safe. You can use it for tea, coffee, curd or other recipes."

    elif name == "bread":
        return "Bread is still safe. Consider making sandwiches or toast before it expires."

    elif name == "rice":
        return "Rice has plenty of time left. Store it properly in a dry place."

    else:
        return f"{name.title()} is safe for now. Keep checking its expiry date."