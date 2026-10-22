
from decimal import Decimal, InvalidOperation
from datetime import date
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date

from .models import Transaction, Category, Budget


@login_required
def home(request):
    today = date.today()

    # Current user's transactions only
    all_transactions = Transaction.objects.filter(
        user=request.user
    ).select_related("category").order_by(
        "-transaction_date", "-created_at"
    )

    total_expense = sum(
        (
            transaction.amount
            for transaction in all_transactions
            if transaction.transaction_type == "EXPENSE"
        ),
        Decimal("0.00"),
    )

    total_income = sum(
        (
            transaction.amount
            for transaction in all_transactions
            if transaction.transaction_type == "INCOME"
        ),
        Decimal("0.00"),
    )

    balance = total_income - total_expense

    monthly_expense = sum(
        (
            transaction.amount
            for transaction in all_transactions
            if transaction.transaction_type == "EXPENSE"
            and transaction.transaction_date.year == today.year
            and transaction.transaction_date.month == today.month
        ),
        Decimal("0.00"),
    )

    # Category-wise expense totals
    category_expenses = {}

    for transaction in all_transactions:
        if transaction.transaction_type == "EXPENSE":
            category_name = transaction.category.name

            if category_name not in category_expenses:
                category_expenses[category_name] = Decimal("0.00")

            category_expenses[category_name] += transaction.amount

    category_expenses_json = json.dumps([
        {
            "category": category,
            "amount": float(amount),
        }
        for category, amount in category_expenses.items()
    ])

    # Current user's monthly expense report
    monthly_report = (
        Transaction.objects
        .filter(
            user=request.user,
            transaction_type="EXPENSE",
        )
        .annotate(month=TruncMonth("transaction_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("-month")
    )

    # Current user's budgets for this month
    current_budgets = Budget.objects.filter(
        user=request.user,
        month__year=today.year,
        month__month=today.month,
    ).select_related("category")

    budget_data = []

    for budget in current_budgets:
        spent = sum(
            (
                transaction.amount
                for transaction in all_transactions
                if transaction.transaction_type == "EXPENSE"
                and transaction.category_id == budget.category_id
                and transaction.transaction_date.year == today.year
                and transaction.transaction_date.month == today.month
            ),
            Decimal("0.00"),
        )

        budget_data.append({
            "category": budget.category.name,
            "limit": budget.monthly_limit,
            "spent": spent,
            "remaining": budget.monthly_limit - spent,
        })

    # Search and transaction type filter
    search_query = request.GET.get("search", "").strip()
    type_filter = request.GET.get("type", "").strip()

    transactions = all_transactions

    if type_filter in ("INCOME", "EXPENSE"):
        transactions = transactions.filter(
            transaction_type=type_filter
        )

    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    context = {
        "transactions": transactions,
        "total_expense": total_expense,
        "total_income": total_income,
        "balance": balance,
        "monthly_expense": monthly_expense,
        "category_expenses": category_expenses,
        "category_expenses_json": category_expenses_json,
        "monthly_report": monthly_report,
        "budget_data": budget_data,
        "categories": Category.objects.filter(user=request.user),
        "search_query": search_query,
        "type_filter": type_filter,
    }

    return render(
        request,
        "transactions/home.html",
        context,
    )


@login_required
@require_POST
def add_transaction(request):
    transaction_type = request.POST.get(
        "transaction_type", ""
    ).strip()

    category_id = request.POST.get("category", "").strip()
    amount = request.POST.get("amount", "").strip()
    description = request.POST.get("description", "").strip()
    transaction_date_value = request.POST.get(
        "transaction_date", ""
    ).strip()
    payment_method = request.POST.get(
        "payment_method", ""
    ).strip()

    if not all([
        transaction_type,
        category_id,
        amount,
        description,
        transaction_date_value,
        payment_method,
    ]):
        messages.error(request, "Please fill in all fields.")
        return redirect("home")

    if transaction_type not in ("INCOME", "EXPENSE"):
        messages.error(request, "Invalid transaction type.")
        return redirect("home")

    valid_payment_methods = {
        choice[0]
        for choice in Transaction.PaymentMethod.choices
    }

    if payment_method not in valid_payment_methods:
        messages.error(request, "Invalid payment method.")
        return redirect("home")

    try:
        category = get_object_or_404(
            Category,
            id=category_id,
            user=request.user,
        )

        if category.category_type != transaction_type:
            messages.error(
                request,
                "Please select a category matching the transaction type.",
            )
            return redirect("home")

        transaction_amount = Decimal(amount)
        parsed_date = parse_date(transaction_date_value)

        if (
            not transaction_amount.is_finite()
            or transaction_amount <= 0
            or parsed_date is None
            or not description
        ):
            raise ValueError

        Transaction.objects.create(
            user=request.user,
            category=category,
            transaction_type=transaction_type,
            amount=transaction_amount,
            description=description,
            transaction_date=parsed_date,
            payment_method=payment_method,
        )

        messages.success(
            request,
            "Transaction added successfully!",
        )

    except (InvalidOperation, ValueError, TypeError):
        messages.error(
            request,
            "Please enter valid transaction details.",
        )

    return redirect("home")


@login_required
@require_POST
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        user=request.user,
    )

    amount = request.POST.get("amount", "").strip()
    description = request.POST.get("description", "").strip()

    try:
        new_amount = Decimal(amount)

        if (
            not new_amount.is_finite()
            or new_amount <= 0
            or not description
        ):
            raise ValueError

        transaction.amount = new_amount
        transaction.description = description
        transaction.save(
            update_fields=[
                "amount",
                "description",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "Transaction updated successfully!",
        )

    except (InvalidOperation, ValueError, TypeError):
        messages.error(
            request,
            "Enter a valid amount and description.",
        )

    return redirect("home")


@login_required
@require_POST
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        user=request.user,
    )

    transaction.delete()

    messages.success(
        request,
        "Transaction deleted successfully!",
    )

    return redirect("home")









