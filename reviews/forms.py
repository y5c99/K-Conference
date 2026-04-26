"""Forms for the reviews app."""

from django import forms
from .models import Review, ConflictOfInterest


class ReviewForm(forms.ModelForm):
    """The written-feedback + recommendation part of a review.
    The numeric scores are handled separately as dynamic fields,
    one per criterion.
    """

    class Meta:
        model = Review
        fields = ('strengths', 'weaknesses', 'additional_comments',
                  'recommendation')
        widgets = {
            'strengths': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What are the strong aspects of this paper?',
            }),
            'weaknesses': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What aspects need to be addressed?',
            }),
            'additional_comments': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Any additional feedback or suggestions for the author',
            }),
        }
        labels = {
            'strengths': 'Strengths *',
            'weaknesses': 'Weaknesses *',
            'additional_comments': 'Additional comments',
            'recommendation': 'Overall Recommendation *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['strengths'].required = True
        self.fields['weaknesses'].required = True
        self.fields['recommendation'].required = True


class ConflictOfInterestForm(forms.ModelForm):
    class Meta:
        model = ConflictOfInterest
        fields = ('reason',)
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Briefly explain the conflict (e.g. co-author, colleague, competitor)',
            }),
        }
        labels = {'reason': 'Reason for recusal *'}


class AssignReviewerForm(forms.Form):
    """Organiser picks a reviewer from a dropdown."""
    reviewer = forms.ModelChoiceField(
        queryset=None,
        empty_label='Select a reviewer',
    )

    def __init__(self, *args, available_reviewers=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_reviewers is not None:
            self.fields['reviewer'].queryset = available_reviewers