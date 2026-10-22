
from django.contrib import admin
from .models import Category, Transaction, Budget


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category_type", "user")
    list_filter = ("category_type",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "transaction_type",
        "amount",
        "category",
        "transaction_date",
        "user",
    )
    list_filter = ("transaction_type", "payment_method")
    search_fields = ("description",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "category",
        "monthly_limit",
        "month",
        "user",
    )
    list_filter = ("month", "category")
