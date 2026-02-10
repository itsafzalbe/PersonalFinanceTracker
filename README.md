Finance Management System (Django)

A Django-based finance management system for managing personal finances, including authentication, budgets, cards, currencies, and transactions.

This project is a web-based Django application built using Class-Based Views (CBVs) and HTML templates.
All functionality mirrors an earlier API-first implementation, but the system has been fully adapted to work as a traditional Django project with server-rendered pages.

⸻

Features

Authentication & User Management
	•	User registration with email verification
	•	Login & logout (session-based authentication)
	•	Profile management (view, update, delete)
	•	Password change
	•	Account statistics dashboard

Budgets
	•	Create, update, delete budgets
	•	Activate / deactivate budgets
	•	Track budget progress
	•	View spending history per budget
	•	Alerts and budget overview
	•	Group budgets by category or time period

Cards & Currencies

Cards
	•	Add, update, and delete cards
	•	Set default card
	•	Update card balance
	•	Card statistics and summaries
	•	Total balance overview

Currencies
	•	View supported currencies
	•	Currency conversion
	•	Exchange rates (latest and historical)

Transactions
	•	Track income and expenses
	•	Categorize transactions
	•	Tag support
	•	Bulk delete transactions
	•	Filter by date, card, or category
	•	Monthly trends and statistics
	•	Recent transactions list

⸻

Tech Stack
	•	Python
	•	Django
	•	Django Templates (HTML)
	•	SQLite (default database)
	•	Django Authentication (sessions)
	•	django-filter

⸻

Project Architecture
	•	Built using Django Class-Based Views
	•	Uses server-rendered templates
	•	Follows Django’s standard project/app structure
	•	CSRF protection enabled by default
	•	Authentication handled via Django sessions


Authentication

This project uses Django’s built-in authentication system:
	•	Session-based login
	•	Secure password hashing
	•	CSRF protection
	•	User permissions enforced at the view level

⸻

Templates

HTML templates are provided for:
	•	Authentication (signup, login, email verification)
	•	Dashboard and statistics
	•	Budgets, cards, and transactions
	•	Create, update, and delete forms



Local Setup

Clone the Repository
```bash

git clone https://github.com/yourusername/finance-management-django.git
cd finance-management-django

```


Create Virtual Environment
```bash

python -m venv venv
source venv/bin/activate

```


Install Dependencies
```bash
pip install -r requirements.txt
```

Environment Variables

Create a .env file in the project root:

```bash
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```


Run the Project
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```


Access the application at:
```bash
http://127.0.0.1:8000/
```


Database
	•	Default database: SQLite
	•	Easily configurable to use PostgreSQL or another database via environment variables

⸻

Notes
	•	This is a full Django web application, not a REST API
	•	Uses HTML templates instead of JSON responses
	•	Designed for direct browser interaction
	•	Business logic and features are unchanged from the original API-based version


    




