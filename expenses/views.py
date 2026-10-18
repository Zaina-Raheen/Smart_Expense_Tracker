import csv
import io
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .categorizer import predict_category
from .forms import ExpenseForm, SignUpForm
from .models import Expense

PERIODS = [
    ('today', 'Today'),
    ('week', 'This week'),
    ('month', 'This month'),
    ('all', 'All time'),
]
PERIOD_LABELS = dict(PERIODS)


def get_period_range(period):
    """Return (start, end) dates for the period, both inclusive.

    None means no limit on that side ("all time" has neither).
    """
    today = date.today()
    if period == 'today':
        return today, today
    if period == 'week':  # weeks run Monday to Sunday
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    if period == 'month':
        start = today.replace(day=1)
        next_month = (start + timedelta(days=32)).replace(day=1)
        return start, next_month - timedelta(days=1)
    return None, None


def apply_period(qs, period):
    start, end = get_period_range(period)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    return qs


def filtered_expenses(request, default_period='month'):
    """Apply the ?period= and ?category= filters to the current user's expenses."""
    period = request.GET.get('period', default_period)
    if period not in PERIOD_LABELS:
        period = default_period
    category = request.GET.get('category', '')
    if category not in dict(Expense.CATEGORY_CHOICES):
        category = ''

    qs = Expense.objects.filter(user=request.user)
    qs = apply_period(qs, period)
    if category:
        qs = qs.filter(category=category)
    return qs, period, category


# ---------- auth ----------

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome, {user.username}. Your account is ready.')
        return redirect('dashboard')
    return render(request, 'registration/signup.html', {'form': form})


# ---------- dashboard ----------

@login_required
def dashboard(request):
    qs, period, _ = filtered_expenses(request)
    qs_all = Expense.objects.filter(user=request.user)

    def total(period_key):
        return apply_period(qs_all, period_key).aggregate(t=Sum('amount'))['t'] or 0

    summary = {
        'today': total('today'),
        'week': total('week'),
        'month': total('month'),
    }

    by_category = list(
        qs.values('category').annotate(total=Sum('amount')).order_by('-total')
    )
    by_date = list(qs.values('date').annotate(total=Sum('amount')).order_by('date'))

    chart_data = {
        'categories': [row['category'] for row in by_category],
        'category_totals': [float(row['total']) for row in by_category],
        'dates': [row['date'].strftime('%d %b') for row in by_date],
        'date_totals': [float(row['total']) for row in by_date],
    }

    context = {
        'summary': summary,
        'period': period,
        'periods': PERIODS,
        'period_label': PERIOD_LABELS[period],
        'period_total': qs.aggregate(t=Sum('amount'))['t'] or 0,
        'period_count': qs.count(),
        'top_category': by_category[0]['category'] if by_category else None,
        'chart_data': chart_data,
        'recent': qs_all[:5],
    }
    return render(request, 'expenses/dashboard.html', context)


# ---------- CRUD ----------

@login_required
def expense_list(request):
    qs, period, category = filtered_expenses(request, default_period='all')
    total = qs.aggregate(t=Sum('amount'))['t'] or 0
    page = Paginator(qs, 15).get_page(request.GET.get('page'))

    # keep filters when moving between pages
    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'page': page,
        'total': total,
        'period': period,
        'periods': PERIODS,
        'category': category,
        'categories': Expense.CATEGORY_CHOICES,
        'querystring': params.urlencode(),
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required
def expense_add(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        expense = form.save(commit=False)
        expense.user = request.user
        expense.save()
        messages.success(request, f'Added "{expense.description}" under {expense.category}.')
        return redirect('expense_list')
    return render(request, 'expenses/expense_form.html', {'form': form, 'editing': False})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    form = ExpenseForm(request.POST or None, instance=expense)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Expense updated.')
        return redirect('expense_list')
    return render(
        request, 'expenses/expense_form.html',
        {'form': form, 'editing': True, 'expense': expense},
    )


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expense_list')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})


@login_required
def predict_api(request):
    """Used by the add/edit form to show the guessed category while typing."""
    return JsonResponse({'category': predict_category(request.GET.get('description', ''))})


# ---------- reports ----------

@login_required
def export_report(request, fmt):
    qs, period, category = filtered_expenses(request, default_period='all')
    total = qs.aggregate(t=Sum('amount'))['t'] or 0
    stamp = date.today().strftime('%Y%m%d')

    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="expenses_{stamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Notes'])
        for e in qs:
            writer.writerow([e.date.isoformat(), e.description, e.category, e.amount, e.notes])
        writer.writerow([])
        writer.writerow(['', '', 'Total', total, ''])
        return response

    if fmt == 'pdf':
        return build_pdf(request.user, qs, total, period, category, stamp)

    return HttpResponse('Unknown format', status=404)


def build_pdf(user, qs, total, period, category, stamp):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title='Expense report',
                            leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    subtitle = f'{user.username} - {PERIOD_LABELS[period]}'
    if category:
        subtitle += f' - {category}'
    elements = [
        Paragraph('Expense report', styles['Title']),
        Paragraph(subtitle, styles['Normal']),
        Paragraph(f'Generated on {date.today():%d %b %Y}', styles['Normal']),
        Spacer(1, 16),
    ]

    data = [['Date', 'Description', 'Category', 'Amount (Rs.)']]
    for e in qs:
        data.append([e.date.strftime('%d %b %Y'), e.description[:45], e.category, f'{e.amount:,.2f}'])
    data.append(['', '', 'Total', f'{total:,.2f}'])

    table = Table(data, colWidths=[80, 220, 90, 100], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#c8cdd3')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f4f6f8')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8ecf0')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)
    doc.build(elements)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="expenses_{stamp}.pdf"'
    return response
    