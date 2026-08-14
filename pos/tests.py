from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Sale, SaleItem


class SaleModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cashier", password="testpass123")
        category = Category.objects.create(name="Drinks")
        self.product = Product.objects.create(
            name="Water", sku="WATER-01", category=category, selling_price=Decimal("500.00"), stock_quantity=10
        )

    def test_sale_rejects_cash_less_than_total(self):
        sale = Sale(
            cashier=self.user,
            payment_method=Sale.PaymentMethod.CASH,
            total=Decimal("1000.00"),
            cash_received=Decimal("500.00"),
            change=Decimal("-500.00"),
        )
        with self.assertRaises(ValidationError):
            sale.full_clean()

    def test_sale_item_calculates_line_total(self):
        sale = Sale.objects.create(
            cashier=self.user,
            payment_method=Sale.PaymentMethod.CARD,
            total=Decimal("1000.00"),
            cash_received=Decimal("1000.00"),
            change=Decimal("0.00"),
        )
        item = SaleItem.objects.create(
            sale=sale,
            product=self.product,
            product_name=self.product.name,
            product_sku=self.product.sku,
            quantity=2,
            unit_price=Decimal("500.00"),
            line_total=Decimal("0.00"),
        )
        self.assertEqual(item.line_total, Decimal("1000.00"))
        self.assertTrue(sale.sale_number.startswith("POS-"))


class PosViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(username="admin", password="adminpass123", email="admin@example.com")
        self.cashier = user_model.objects.create_user(username="cashier", password="cashierpass123")
        self.category = Category.objects.create(name="Snacks")
        self.product = Product.objects.create(
            name="Chips", sku="CHIPS-01", category=self.category, selling_price=Decimal("1000.00"), stock_quantity=3
        )

    def _set_cart(self, quantity):
        session = self.client.session
        session["cart"] = {str(self.product.id): quantity}
        session.save()

    def test_cashier_cannot_open_admin_management_pages(self):
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse("product_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("sales_report")).status_code, 403)

    def test_admin_can_create_a_product(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("product_create"),
            {
                "name": "Cookie",
                "sku": "COOKIE-01",
                "category": self.category.id,
                "selling_price": "700.00",
                "stock_quantity": 8,
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("product_list"))
        self.assertTrue(Product.objects.filter(sku="COOKIE-01").exists())

    def test_admin_dashboard_and_workspace_pages_render(self):
        self.client.force_login(self.admin)
        for url_name in ("dashboard", "pos_sale", "product_list", "sales_report"):
            with self.subTest(url_name=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_cart_add_and_update(self):
        self.client.force_login(self.cashier)
        response = self.client.post(reverse("cart_add", args=[self.product.id]), {"quantity": 1})
        self.assertRedirects(response, reverse("pos_sale"))
        self.assertEqual(self.client.session["cart"][str(self.product.id)], 1)
        self.client.post(reverse("cart_update"), {f"quantity_{self.product.id}": 2})
        self.assertEqual(self.client.session["cart"][str(self.product.id)], 2)

    def test_successful_cash_checkout_reduces_stock_once(self):
        self.client.force_login(self.cashier)
        self._set_cart(2)
        response = self.client.post(
            reverse("checkout"), {"payment_method": Sale.PaymentMethod.CASH, "cash_received": "2500.00"}
        )
        sale = Sale.objects.get()
        self.assertRedirects(response, reverse("receipt", args=[sale.id]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1)
        self.assertEqual(sale.total, Decimal("2000.00"))
        self.assertEqual(sale.change, Decimal("500.00"))
        self.assertEqual(sale.items.count(), 1)
        self.assertEqual(self.client.session["cart"], {})

    def test_insufficient_stock_does_not_create_sale(self):
        self.client.force_login(self.cashier)
        self._set_cart(4)
        response = self.client.post(
            reverse("checkout"), {"payment_method": Sale.PaymentMethod.CASH, "cash_received": "5000.00"}
        )
        self.assertRedirects(response, reverse("pos_sale"))
        self.assertFalse(Sale.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_cashier_can_only_view_own_receipt(self):
        other = get_user_model().objects.create_user(username="other", password="otherpass123")
        sale = Sale.objects.create(
            cashier=other,
            payment_method=Sale.PaymentMethod.CARD,
            total=Decimal("100.00"),
            cash_received=Decimal("100.00"),
            change=Decimal("0.00"),
        )
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse("receipt", args=[sale.id])).status_code, 403)
