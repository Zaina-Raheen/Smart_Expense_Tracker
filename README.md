# Smart Expense Tracker (Django)

Track daily, weekly and monthly expenses, auto-detect categories from the description, view charts, and download reports as CSV or PDF.

## Run it

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/ and create an account from the Sign up link.

Optional: `python manage.py seed_demo` creates a demo user (`demo` / `demo12345`) with sample expenses.
Run the tests with `python manage.py test`.

Charts and Bootstrap load from a CDN, so the first page load needs internet.

## Features

| Feature | Where |
|---|---|
| Sign up, log in, log out (Django auth) | `/signup/`, `/login/` |
| Per-user data isolation | every query filters on `request.user` |
| Add / edit / delete expenses | `/expenses/`, edit form is pre-filled |
| Smart category prediction | `expenses/categorizer.py` (keyword dictionary) |
| Today / this week / this month filter | dashboard and expense list |
| Category pie chart, spending-over-time bar chart | dashboard (Chart.js) |
| Download report (CSV / PDF) | buttons on the expense list, respects current filters |

## Project layout

```
config/            settings, root urls
expenses/
  models.py        Expense model
  categorizer.py   keyword -> category logic
  forms.py         signup and expense forms
  views.py         dashboard, CRUD, filters, CSV/PDF export
  tests.py         12 tests
templates/         base, auth pages, dashboard, list, form, delete
static/            css/style.css, js/charts.js, js/form.js
```

## Customising the categories

Open `expenses/categorizer.py` and add words to `CATEGORY_KEYWORDS`. To use NLP later, replace the body of `predict_category()`; nothing else needs to change.

## Notes

- Currency is shown as Rs.; change it in the templates and `views.py` (PDF) if you need another.
- Weeks start on Monday.
- Before deploying, set `DEBUG = False`, a new `SECRET_KEY` and `ALLOWED_HOSTS` in `config/settings.py`.
