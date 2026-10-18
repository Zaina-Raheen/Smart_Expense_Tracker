from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .categorizer import predict_category
from .models import Expense


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ExpenseForm(forms.ModelForm):
    # Blank choice = let the app guess from the description.
    category = forms.ChoiceField(
        choices=[('', 'Auto-detect from description')] + Expense.CATEGORY_CHOICES,
        required=False,
    )

    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date', 'category', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'e.g. Uber to office'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-select' if name == 'category' else 'form-control'
            field.widget.attrs['class'] = css

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('category'):
            cleaned['category'] = predict_category(cleaned.get('description', ''))
        return cleaned
