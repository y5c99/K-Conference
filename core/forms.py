"""Forms for the core app."""

from django import forms
from .models import Announcement, FAQ


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'body', 'audience', 'is_pinned')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Announcement title'}),
            'body':  forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Write your announcement here...',
            }),
        }


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ('question', 'answer', 'order', 'is_published')
        widgets = {
            'question': forms.TextInput(attrs={
                'placeholder': 'e.g. When does registration close?',
            }),
            'answer': forms.Textarea(attrs={'rows': 4}),
        }