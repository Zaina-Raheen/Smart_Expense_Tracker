from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .categorizer import predict_category
from .models import Expense


class CategorizerTests(TestCase):
    def test_known_keywords(self):
        self.assertEqual(predict_category('Uber to airport'), 'Travel')
        self.assertEqual(predict_category('Pizza night'), 'Food')
        self.assertEqual(predict_category('Netflix'), 'Entertainment')
        self.assertEqual(predict_category('Electricity bill'), 'Bills')

    def test_unknown_goes_to_other(self):
        self.assertEqual(predict_category('random thing'), 'Other')
        self.assertEqual(predict_category(''), 'Other')


class ExpenseViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('asha', password='pass12345')
        self.other = User.objects.create_user('ravi', password='pass12345')
        self.client.login(username='asha', password='pass12345')

    def make(self, user=None, desc='Lunch', amount='100', days_ago=0, category='Food'):
        return Expense.objects.create(
            user=user or self.user, description=desc, amount=amount,
            date=date.today() - timedelta(days=days_ago), category=category,
        )

    def test_login_required(self):
        self.client.logout()
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])

    def test_add_auto_category(self):
        self.client.post(reverse('expense_add'), {
            'description': 'Uber ride', 'amount': '250', 'date': date.today().isoformat(),
            'category': '', 'notes': '',
        })
        e = Expense.objects.get()
        self.assertEqual(e.category, 'Travel')
        self.assertEqual(e.user, self.user)

    def test_add_manual_category_wins(self):
        self.client.post(reverse('expense_add'), {
            'description': 'Uber ride', 'amount': '250', 'date': date.today().isoformat(),
            'category': 'Other', 'notes': '',
        })
        self.assertEqual(Expense.objects.get().category, 'Other')

    def test_edit_prefills_and_saves(self):
        e = self.make()
        r = self.client.get(reverse('expense_edit', args=[e.pk]))
        self.assertContains(r, 'value="Lunch"')
        self.client.post(reverse('expense_edit', args=[e.pk]), {
            'description': 'Dinner', 'amount': '300', 'date': e.date.isoformat(),
            'category': 'Food', 'notes': 'late',
        })
        e.refresh_from_db()
        self.assertEqual(e.description, 'Dinner')

    def test_delete(self):
        e = self.make()
        self.client.post(reverse('expense_delete', args=[e.pk]))
        self.assertFalse(Expense.objects.exists())

    def test_users_cannot_touch_each_others_data(self):
        theirs = self.make(user=self.other, desc='Secret')
        self.assertEqual(self.client.get(reverse('expense_edit', args=[theirs.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('expense_delete', args=[theirs.pk])).status_code, 404)
        r = self.client.get(reverse('expense_list'))
        self.assertNotContains(r, 'Secret')

    def test_period_filters(self):
        self.make(desc='today item', days_ago=0)
        self.make(desc='old item', days_ago=90)
        r = self.client.get(reverse('expense_list'), {'period': 'today'})
        self.assertContains(r, 'today item')
        self.assertNotContains(r, 'old item')
        r = self.client.get(reverse('expense_list'), {'period': 'all'})
        self.assertContains(r, 'old item')

    def test_period_filters_exclude_future_dates(self):
        self.make(desc='today item', days_ago=0)
        self.make(desc='tomorrow item', days_ago=-1)
        self.make(desc='next year item', days_ago=-400)
        r = self.client.get(reverse('expense_list'), {'period': 'today'})
        self.assertContains(r, 'today item')
        self.assertNotContains(r, 'tomorrow item')
        r = self.client.get(reverse('expense_list'), {'period': 'month'})
        self.assertNotContains(r, 'next year item')

    def test_csv_and_pdf_export(self):
        self.make(desc='Lunch', amount='99.50')
        r = self.client.get(reverse('export_report', args=['csv']))
        self.assertEqual(r['Content-Type'], 'text/csv')
        self.assertIn('Lunch', r.content.decode())
        r = self.client.get(reverse('export_report', args=['pdf']))
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))

    def test_dashboard_renders(self):
        self.make()
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_signup_logs_in(self):
        self.client.logout()
        r = self.client.post(reverse('signup'), {
            'username': 'newuser', 'email': '', 'password1': 'S0meStrongPass!', 'password2': 'S0meStrongPass!',
        })
        self.assertRedirects(r, reverse('dashboard'))