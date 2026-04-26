"""Reusable helpers for the reviews app."""

from .models import ReviewCriterion


DEFAULT_CRITERIA = [
    {'name': 'Originality',
     'description': 'Does the work present novel ideas or approaches?',
     'order': 1},
    {'name': 'Technical Quality',
     'description': 'Is the technical approach sound and rigorous?',
     'order': 2},
    {'name': 'Clarity of Writing',
     'description': 'Is the paper well-written and easy to understand?',
     'order': 3},
    {'name': 'Relevance to Track',
     'description': 'Does it fit the conference themes and track?',
     'order': 4},
]


def seed_default_criteria(conference):
    """Create the standard 4-criterion rubric for a conference (1-5 scale)."""
    for c in DEFAULT_CRITERIA:
        ReviewCriterion.objects.get_or_create(
            conference=conference,
            name=c['name'],
            defaults={
                'description': c['description'],
                'order': c['order'],
                'weight': 1,
                'min_score': 1,
                'max_score': 5,
            },
        )