import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Review, Profile, Subscription


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Логин'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Повторите пароль'})

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Логин'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ваш отзыв'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'phone', 'birth_date', 'bio']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996 XXX XXX XXX'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Пара слов о себе'}),
        }


# ============ ОПЛАТА КАРТОЙ (симуляция) ============

class CardPaymentForm(forms.Form):
    """Симуляция оплаты: только 16-значный номер карты"""
    card_number = forms.CharField(
        label='Номер карты',
        max_length=19,
        min_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0000 0000 0000 0000',
            'autocomplete': 'off',
            'inputmode': 'numeric',
        })
    )

    def clean_card_number(self):
        raw = self.cleaned_data['card_number']
        # Убираем пробелы и дефисы
        digits = re.sub(r'[\s\-]', '', raw)
        if not digits.isdigit():
            raise forms.ValidationError('Номер карты должен содержать только цифры')
        if len(digits) != 16:
            raise forms.ValidationError('Номер карты должен состоять из 16 цифр')
        return digits

    @property
    def last4(self):
        digits = self.cleaned_data.get('card_number', '')
        return digits[-4:] if len(digits) >= 4 else '0000'


class TicketPaymentForm(CardPaymentForm):
    """Оплата билета — та же форма карты"""
    pass


# ============ ПОДПИСКА ============

class SubscriptionForm(forms.Form):
    plan = forms.ChoiceField(
        label='Тариф',
        choices=Subscription.PLAN_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    card_number = forms.CharField(
        label='Номер карты',
        max_length=19,
        min_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0000 0000 0000 0000',
            'autocomplete': 'off',
            'inputmode': 'numeric',
        })
    )

    def clean_card_number(self):
        raw = self.cleaned_data['card_number']
        digits = re.sub(r'[\s\-]', '', raw)
        if not digits.isdigit():
            raise forms.ValidationError('Номер карты должен содержать только цифры')
        if len(digits) != 16:
            raise forms.ValidationError('Номер карты должен состоять из 16 цифр')
        return digits

    @property
    def last4(self):
        digits = self.cleaned_data.get('card_number', '')
        return digits[-4:] if len(digits) >= 4 else '0000'