def cart_summary(request):
    """Expose a safe cart quantity to the navigation on every page."""
    cart = request.session.get("cart", {})
    count = 0
    for quantity in cart.values():
        try:
            count += max(0, int(quantity))
        except (TypeError, ValueError):
            continue
    return {"nav_cart_count": count}
