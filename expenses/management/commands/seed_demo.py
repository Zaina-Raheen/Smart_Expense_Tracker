import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from expenses.categorizer import predict_category
from expenses.models import Expense

SAMPLES = [
    ('Uber to office', 180), ('Pizza with friends', 450), ('Netflix subscription', 649),
    ('Electricity bill', 1250), ('Medicine from pharmacy', 320), ('Amazon headphones', 1799),
    ('Coffee', 120), ('Metro card recharge', 500), ('Udemy course', 499), ('Groceries', 860),
    ('Movie tickets', 600), ('Petrol', 900), ('Wifi recharge', 799), ('Lunch', 150),
]


class Command(BaseCommand):
    help = 'Create a demo user (demo / demo12345) with sample expenses.'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='demo')
        if created:
            user.set_password('demo12345')
            user.save()
        if user.expenses.exists():
            self.stdout.write('Demo user already has expenses - nothing added.')
            return
        random.seed(7)
        for i in range(35):
            desc, base = random.choice(SAMPLES)
            Expense.objects.create(
                user=user,
                description=desc,
                amount=Decimal(base) + Decimal(random.randint(-20, 40)),
                date=date.today() - timedelta(days=random.randint(0, 40)),
                category=predict_category(desc),
            )
        self.stdout.write(self.style.SUCCESS('Demo data ready. Login: demo / demo12345'))
