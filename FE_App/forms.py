from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo', widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}))
    first_name = forms.CharField(required=True, label='Nombre', widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'}))
    last_name = forms.CharField(required=True, label='Apellido', widget=forms.TextInput(attrs={'placeholder': 'Tu apellido'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo electrónico.')
        return email
