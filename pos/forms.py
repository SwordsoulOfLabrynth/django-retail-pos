from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import Category, Product, Sale


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "sku", "category", "selling_price", "stock_quantity", "is_active"]
        widgets = {"selling_price": forms.NumberInput(attrs={"min": "0", "step": "0.01"})}


class StockAdjustmentForm(BootstrapFormMixin, forms.Form):
    adjustment = forms.IntegerField(
        help_text="Use a positive number to add stock or a negative number to remove stock.",
        widget=forms.NumberInput(attrs={"step": "1"}),
    )

    def __init__(self, *args, product=None, **kwargs):
        self.product = product
        super().__init__(*args, **kwargs)

    def clean_adjustment(self):
        adjustment = self.cleaned_data["adjustment"]
        if adjustment == 0:
            raise ValidationError("Enter a stock adjustment other than zero.")
        if self.product and self.product.stock_quantity + adjustment < 0:
            raise ValidationError("This adjustment would make stock negative.")
        return adjustment


class CheckoutForm(BootstrapFormMixin, forms.Form):
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices)
    cash_received = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
    )

    def __init__(self, *args, total=None, **kwargs):
        self.total = total
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("payment_method") == Sale.PaymentMethod.CASH:
            cash_received = cleaned_data.get("cash_received")
            if cash_received is None:
                self.add_error("cash_received", "Enter the amount received from the customer.")
            elif self.total is not None and cash_received < self.total:
                self.add_error("cash_received", "Cash received must cover the sale total.")
        return cleaned_data
