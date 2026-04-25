"""Forms used in the conference app."""

from django import forms
from .models import Conference, Track, Session, Registration


class ConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = (
            'name', 'short_name', 'description',
            'start_date', 'end_date',
            'location', 'online_link', 'mode',
            'capacity',
            'submission_deadline', 'review_deadline',
            'status', 'code_of_conduct',
        )
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'submission_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'review_deadline':     forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description':         forms.Textarea(attrs={'rows': 3}),
            'code_of_conduct':     forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'End date must be on or after the start date.')
        return cleaned


class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ('name', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ('title', 'kind', 'track', 'speaker', 'location',
                  'starts_at', 'ends_at', 'description')
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at':   forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, conference=None, **kwargs):
        super().__init__(*args, **kwargs)
        if conference is not None:
            # Only show tracks that belong to this conference.
            self.fields['track'].queryset = conference.tracks.all()


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ('accessibility_needs',)
        widgets = {
            'accessibility_needs': forms.Textarea(
                attrs={'rows': 2, 'placeholder': 'Optional — anything we should know?'}
            ),
        }