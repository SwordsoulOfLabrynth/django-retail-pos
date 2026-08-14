from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from pos.models import Category, Product


class Command(BaseCommand):
    help = "Create sample POS categories, products, and demo accounts."

    def handle(self, *args, **options):
        user_model = get_user_model()
        admin, created = user_model.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))
        cashier, created = user_model.objects.get_or_create(username="cashier", defaults={"email": "cashier@example.com"})
        if created:
            cashier.set_password("cashier123")
            cashier.save()
            self.stdout.write(self.style.SUCCESS("Created cashier user: cashier / cashier123"))

        drinks, _ = Category.objects.get_or_create(name="Drinks")
        snacks, _ = Category.objects.get_or_create(name="Snacks")
        household, _ = Category.objects.get_or_create(name="Household")
        products = [
            ("Bottled Water", "DRK-001", drinks, "500.00", 30),
            ("Orange Juice", "DRK-002", drinks, "1500.00", 18),
            ("Potato Chips", "SNK-001", snacks, "1200.00", 25),
            ("Chocolate Bar", "SNK-002", snacks, "1000.00", 20),
            ("Tissue Pack", "HOM-001", household, "900.00", 12),
        ]
        for name, sku, category, price, stock in products:
            Product.objects.get_or_create(
                sku=sku,
                defaults={"name": name, "category": category, "selling_price": price, "stock_quantity": stock},
            )
        self.stdout.write(self.style.SUCCESS("Sample catalog is ready."))
