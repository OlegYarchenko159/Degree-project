# -*- coding: utf-8 -*-
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином не зарегистрирован в системе!')

        user = User.objects.get(username=username)
        if user and not user.check_password(password):
            raise forms.ValidationError('Неверный пароль!')


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_check = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'password_check',
            'first_name',
            'last_name',
            'email',
        ]

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
        self.fields['password'].help_text = 'Придумайте пароль'
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['email'].label = 'Ваша почта'
        self.fields['email'].help_text = 'Пожалуйста указывайте реальный адрес'
        self.fields['password_check'].label = 'Повторите пароль'

    def clean(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        password_check = self.cleaned_data['password_check']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже зарегистрирован в системе!')
        if password != password_check:
            raise forms.ValidationError('Ваши пароли не совпадают, попробуйте ещё раз!')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким почтовым адресом уже зарегистрирован в системе!')


class OrderForm(forms.Form):
    name = forms.CharField()
    last_name = forms.CharField(required=False)
    phone = forms.CharField()
    buying_type = forms.ChoiceField(widget=forms.Select(), choices=(('self', 'Самовывоз'),
                                                                    ('delivery', 'Доставка')))
    data = forms.DateField(widget=forms.SelectDateWidget(), initial=timezone.now())
    address = forms.CharField(required=False)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Имя"
        self.fields['last_name'].label = "Фамилия"
        self.fields['phone'].label = "Контакный телефон"
        self.fields['phone']. help_text = "Пожалуйста, указывайте реальный номер телефона, по которому с Вами можно связаться"
        self.fields['buying_type'].label = "Способ получения"
        self.fields['address'].label = "Адрес доставки"
        self.fields['address'].help_text = "Обязательно указывайте город"
        self.fields['comments'].label = "Комментарии к заказу"
        self.fields['data'].label = "Дата доставки"
        self.fields['data'].help_text = "Доставка производиться на следующий день после заказа"