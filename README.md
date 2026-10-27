# 🛒 Retail POS — Django Certificate Project

> A robust, server-rendered point-of-sale application built with Django and SQLite, featuring atomic checkouts, stock protection, receipt printing, role-based cashier management, and automated test suites.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=flat-square&logo=django&logoColor=white)](https://djangoproject.com/)
[![Database](https://img.shields.io/badge/SQLite-ACID%20Compliant-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat-square&logo=pytest)](https://docs.djangoproject.com/en/5.0/topics/testing/)
[![Status](https://img.shields.io/badge/Certification-Coursework%20Project-blue?style=flat-square)](https://github.com/SwordsoulOfLabrynth/django-retail-pos)

---

## Features

- **Role-Based Authentication**: Separate Administrator and Cashier privileges via Django's auth system
- **Inventory Management**: Category and product catalog management with automated low-stock warnings
- **Session-Based Cart**: Fast, server-side cart operations with quantity adjustment and clearing
- **Atomic Checkout Engine**: Enforces database atomicity to prevent stock overdraft and records itemized ledger entries
- **Tender Methods**: Cash and card checkout with automatic change computation
- **Printable Receipts**: Formal customer receipts with unique receipt numbering
- **Daily Sales Reporting**: Admin-only audit dashboard computing daily revenue totals
- **Automated Test Coverage**: Comprehensive test suite verifying permissions, checkout transactions, and edge cases

---

## Setup

Use Python 3.13+ and run the following commands from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_pos
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in a browser.

Demo accounts created by `seed_pos`:

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `admin` | `admin123` |
| Cashier | `cashier` | `cashier123` |

*Note: Change these credentials before using outside demonstration environments.*

---

## Demonstration Flow

1. Sign in as `admin`; create a category/product or adjust inventory.
2. Sign out and sign in as `cashier`.
3. Start a new sale, add products, update the cart, and select cash or card.
4. Complete checkout and print the generated receipt.
5. Sign back in as `admin` and open **Reports** to view the daily sales total.

---

## Verification & Testing

```powershell
python manage.py test
```

The test suite covers receipt calculations, permission gates, product creation, cart updates, successful checkout, stock protection, and receipt ownership.
