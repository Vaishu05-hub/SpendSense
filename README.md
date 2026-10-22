
# SpendSense – Personal Expense Tracker

## About the Project
SpendSense is a web-based personal finance management application developed using Python and Django. It helps users manage income, expenses, monthly budgets, and spending reports.

## Features
- Add, edit, and delete transactions
- Track income and expenses
- Search and filter transactions
- Manage monthly budgets
- View category-wise expense charts
- View monthly expense reports
- Django Admin integration

## Technologies Used
- Frontend: HTML, CSS, JavaScript
- Backend: Python, Django
- Database: PostgreSQL
- Charts: Chart.js
- Version Control: Git and GitHub

## Installation

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install Django and the required PostgreSQL driver.
4. Configure PostgreSQL credentials in `config/settings.py`.
5. Run database migrations.
6. Create an administrator account.
7. Start the Django development server.

## Run the Project

```bash
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Future Enhancements
- Savings goal tracking
- Downloadable expense reports
- Improved financial insights

## License
This project uses the MIT License.
