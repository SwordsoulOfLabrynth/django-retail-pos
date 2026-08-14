from datetime import date
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Count, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate

from .forms import CategoryForm, CheckoutForm, ProductForm, StockAdjustmentForm
from .models import Category, Product, Sale, SaleItem


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Only administrators can access this page.")
        return view_func(request, *args, **kwargs)

    return wrapped


def _cart(request):
    return request.session.get("cart", {})


def _set_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def cart_details(request):
    cart = _cart(request)
    products = Product.objects.filter(id__in=cart.keys(), is_active=True).select_related("category")
    products_by_id = {str(product.id): product for product in products}
    items = []
    total = Decimal("0.00")
    for product_id, quantity in cart.items():
        product = products_by_id.get(str(product_id))
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if product and quantity > 0:
            line_total = product.selling_price * quantity
            items.append({"product": product, "quantity": quantity, "line_total": line_total})
            total += line_total
    return items, total


@login_required
def dashboard(request):
    context = {}
    if request.user.is_superuser:
        today_sales = Sale.objects.filter(created_at__date=localdate())
        context.update(
            {
                "today_sale_count": today_sales.count(),
                "today_revenue": today_sales.aggregate(total=Sum("total"))["total"] or Decimal("0.00"),
                "total_products": Product.objects.count(),
                "total_stock": Product.objects.aggregate(total=Sum("stock_quantity"))["total"] or 0,
                "category_count": Category.objects.count(),
                "low_stock_products": Product.objects.filter(is_active=True, stock_quantity__lte=5).order_by("stock_quantity", "name")[:8],
                "recent_sales": Sale.objects.select_related("cashier")[:5],
            }
        )
    else:
        context["recent_sales"] = Sale.objects.filter(cashier=request.user)[:5]
    return render(request, "pos/dashboard.html", context)


@login_required
@admin_required
def product_list(request):
    return render(request, "pos/product_list.html", {"products": Product.objects.select_related("category")})


@login_required
@admin_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product created.")
        return redirect("product_list")
    return render(request, "pos/product_form.html", {"form": form, "title": "Add product"})


@login_required
@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("product_list")
    return render(request, "pos/product_form.html", {"form": form, "title": "Edit product"})


@login_required
@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        try:
            product.delete()
        except ProtectedError:
            messages.error(request, "Products included in completed sales cannot be deleted. Mark it inactive instead.")
            return redirect("product_list")
        messages.success(request, "Product deleted.")
        return redirect("product_list")
    return render(request, "pos/confirm_delete.html", {"object": product, "cancel_url": "product_list"})


@login_required
@admin_required
def stock_adjust(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockAdjustmentForm(request.POST or None, product=product)
    if request.method == "POST" and form.is_valid():
        product.stock_quantity += form.cleaned_data["adjustment"]
        product.save(update_fields=["stock_quantity"])
        messages.success(request, f"Stock updated. {product.name} now has {product.stock_quantity} units.")
        return redirect("product_list")
    return render(request, "pos/stock_adjust.html", {"form": form, "product": product})


@login_required
@admin_required
def category_list(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect("category_list")
    return render(request, "pos/category_list.html", {"form": form, "categories": Category.objects.all()})


@login_required
@admin_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect("category_list")
    return render(request, "pos/category_form.html", {"form": form, "category": category})


@login_required
@admin_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        try:
            category.delete()
        except ProtectedError:
            messages.error(request, "A category with products cannot be deleted.")
            return redirect("category_list")
        messages.success(request, "Category deleted.")
        return redirect("category_list")
    return render(request, "pos/confirm_delete.html", {"object": category, "cancel_url": "category_list"})


@login_required
def pos_sale(request):
    items, total = cart_details(request)
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0).select_related("category")
    return render(request, "pos/pos_sale.html", {"products": products, "cart_items": items, "cart_total": total})


@login_required
def cart_add(request, product_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 0
    if quantity < 1:
        messages.error(request, "Quantity must be at least one.")
        return redirect("pos_sale")
    cart = _cart(request)
    current_quantity = int(cart.get(str(product.id), 0))
    if current_quantity + quantity > product.stock_quantity:
        messages.error(request, f"Only {product.stock_quantity} units of {product.name} are available.")
    else:
        cart[str(product.id)] = current_quantity + quantity
        _set_cart(request, cart)
        messages.success(request, f"{product.name} added to cart.")
    return redirect("pos_sale")


@login_required
def cart_update(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    cart = _cart(request)
    products = Product.objects.in_bulk([int(product_id) for product_id in cart.keys()])
    for product_id in list(cart.keys()):
        try:
            quantity = int(request.POST.get(f"quantity_{product_id}", cart[product_id]))
        except ValueError:
            quantity = 0
        product = products.get(int(product_id))
        if not product or quantity <= 0:
            cart.pop(product_id, None)
        elif quantity > product.stock_quantity:
            cart[product_id] = product.stock_quantity
            messages.warning(request, f"{product.name} was limited to available stock ({product.stock_quantity}).")
        else:
            cart[product_id] = quantity
    _set_cart(request, cart)
    messages.success(request, "Cart updated.")
    return redirect("pos_sale")


@login_required
def cart_clear(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    _set_cart(request, {})
    messages.success(request, "Cart cleared.")
    return redirect("pos_sale")


@login_required
def checkout(request):
    cart_items, cart_total = cart_details(request)
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect("pos_sale")
    form = CheckoutForm(request.POST or None, total=cart_total)
    if request.method == "POST" and form.is_valid():
        cart = _cart(request)
        with transaction.atomic():
            products = Product.objects.select_for_update().filter(id__in=cart.keys(), is_active=True)
            locked_products = {str(product.id): product for product in products}
            sale_items = []
            actual_total = Decimal("0.00")
            for product_id, quantity in cart.items():
                product = locked_products.get(str(product_id))
                quantity = int(quantity)
                if not product or quantity < 1 or product.stock_quantity < quantity:
                    messages.error(request, "Stock changed before checkout. Please review your cart.")
                    return redirect("pos_sale")
                line_total = product.selling_price * quantity
                actual_total += line_total
                sale_items.append((product, quantity, line_total))

            payment_method = form.cleaned_data["payment_method"]
            cash_received = form.cleaned_data["cash_received"] or Decimal("0.00")
            if payment_method == Sale.PaymentMethod.CARD:
                cash_received = actual_total
            elif cash_received < actual_total:
                messages.error(request, "The sale total changed. Cash received no longer covers the total.")
                return redirect("pos_sale")
            sale = Sale.objects.create(
                cashier=request.user,
                payment_method=payment_method,
                total=actual_total,
                cash_received=cash_received,
                change=cash_received - actual_total,
            )
            for product, quantity, line_total in sale_items:
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    quantity=quantity,
                    unit_price=product.selling_price,
                    line_total=line_total,
                )
                product.stock_quantity -= quantity
                product.save(update_fields=["stock_quantity"])
        _set_cart(request, {})
        messages.success(request, "Sale completed successfully.")
        return redirect("receipt", pk=sale.pk)
    return render(request, "pos/checkout.html", {"form": form, "cart_items": cart_items, "cart_total": cart_total})


@login_required
def receipt(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("cashier").prefetch_related("items"), pk=pk)
    if not request.user.is_superuser and sale.cashier_id != request.user.id:
        raise PermissionDenied("You can only view your own receipts.")
    return render(request, "pos/receipt.html", {"sale": sale})


@login_required
@admin_required
def sales_report(request):
    date_text = request.GET.get("date", localdate().isoformat())
    try:
        selected_date = date.fromisoformat(date_text)
    except ValueError:
        selected_date = localdate()
        messages.error(request, "Enter a valid date.")
    sales = Sale.objects.filter(created_at__date=selected_date).select_related("cashier")
    payment_breakdown = sales.values("payment_method").annotate(total=Sum("total"), count=Count("id"))
    return render(
        request,
        "pos/sales_report.html",
        {
            "sales": sales,
            "selected_date": selected_date.isoformat(),
            "sale_count": sales.count(),
            "revenue": sales.aggregate(total=Sum("total"))["total"] or Decimal("0.00"),
            "payment_breakdown": payment_breakdown,
        },
    )
