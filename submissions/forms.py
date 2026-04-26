"""Forms for the submissions app."""

from django import forms
from .models import Submission, SubmissionFile
from .validators import validate_manuscript_file


class SubmissionForm(forms.ModelForm):
    """
    Form for creating/editing a submission's metadata.
    The file is handled separately (see SubmissionFileForm) so the
    author can save a draft without uploading and re-upload later.
    """

    class Meta:
        model = Submission
        fields = ('title', 'abstract', 'track', 'keywords', 'co_authors')
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter your paper title',
            }),
            'abstract': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Enter paper abstract (max 300 words)',
                'maxlength': '3000',
            }),
            'keywords': forms.TextInput(attrs={
                'placeholder': 'e.g. machine learning, healthcare, privacy',
            }),
            'co_authors': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'One per line: Name, email, affiliation',
            }),
        }

    def __init__(self, *args, conference=None, **kwargs):
        super().__init__(*args, **kwargs)
        if conference is not None:
            tracks = conference.tracks.all()
            if tracks.exists():
                # Conference has tracks — show the dropdown
                self.fields['track'].queryset = tracks
                self.fields['track'].empty_label = 'Select a track'
                self.fields['track'].required = True
            else:
                # No tracks defined — hide the field entirely
                self.fields.pop('track', None)

    def clean_abstract(self):
        abstract = self.cleaned_data.get('abstract', '').strip()
        word_count = len(abstract.split())
        if word_count > 300:
            raise forms.ValidationError(
                f'Abstract is {word_count} words. Please keep it under 300.'
            )
        return abstract


class SubmissionFileForm(forms.Form):
    """Form just for the manuscript file upload."""

    file = forms.FileField(
        label='Manuscript file',
        help_text='PDF, DOC, or DOCX — max 25 MB.',
        validators=[validate_manuscript_file],
    )
class DecisionForm(forms.Form):
    """Organiser's accept/reject decision."""

    DECISION_ACCEPT = 'accepted'
    DECISION_REJECT = 'rejected'
    DECISION_REVIEW = 'under_review'  # send back to review

    DECISION_CHOICES = [
        (DECISION_ACCEPT, 'Accept'),
        (DECISION_REJECT, 'Reject'),
        (DECISION_REVIEW, 'Keep Under Review'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect,
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional notes for internal records or to share with author.',
        }),
        required=False,
        label='Decision notes',
    )