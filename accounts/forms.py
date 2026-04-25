"""
Forms for the 'accounts' app.

We use Django's built-in UserCreationForm (which already handles
secure password creation) and extend it with our extra fields.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile


class SignUpDetailsForm(UserCreationForm):
    """
    Step 2 of signup: name, email, organisation, password.
    Username is auto-generated from the email.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
    )
    affiliation = forms.CharField(
        max_length=200,
        required=True,
        label='Organisation/Affiliation',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your organisation'}),
    )

    agree_terms = forms.BooleanField(
        required=True,
        label='I agree to the Terms of Service and Privacy Policy',
    )

    class Meta:
        model = User
        # Note: no 'username' — we'll generate it from the email.
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customise the password field placeholders/labels.
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'placeholder': 'Enter your password'}
        )
        self.fields['password1'].label = 'Password'
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'placeholder': 'Confirm your password'}
        )
        self.fields['password2'].label = 'Confirm Password'

    def clean_email(self):
        """Make sure the email isn't already used."""
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # Use the email as the username (simpler for users).
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailLoginForm(AuthenticationForm):
    """
    Login form using email + password instead of username + password.
    """
    username = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput(
            attrs={'placeholder': 'Enter your password'}
        )