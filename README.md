# Retail POS — Django Certificate Project

A small, server-rendered point-of-sale application built with Django and SQLite. It is intended for classroom demonstration and portfolio submission.

## Features

- Admin and cashier accounts using Django authentication
- Category and product management, including stock adjustment
- Session-based shopping cart with quantity updates and clearing
- Cash or card checkout with change calculation for cash payments
- Atomic checkout that prevents negative stock and records an itemized sale
- Printable sale receipts and an admin-only daily sales report
- Django admin for secondary data management

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

Open `http://127.0.0.1:8000/` in a browser.

Demo accounts created by `seed_pos`:

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `admin` | `admin123` |
| Cashier | `cashier` | `cashier123` |

Change these passwords before using the project outside a classroom demonstration.

## Demonstration flow

1. Sign in as `admin`; create a category/product or adjust inventory.
2. Sign out and sign in as `cashier`.
3. Start a new sale, add products, update the cart, and select cash or card.
4. Complete checkout and print the generated receipt.
5. Sign back in as `admin` and open **Reports** to view the daily sales total.

## Verification

```powershell
python manage.py test
```

The test suite covers receipt calculations, permissions, product creation, cart updates, successful checkout, stock protection, and receipt ownership.
