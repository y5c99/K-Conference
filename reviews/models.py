"""
Models for the 'reviews' app.

ReviewCriterion: a single scoring axis (e.g. "Originality", scored 1-5).
Tied to a conference so each event can have its own rubric.

Review: one reviewer's assignment to one submission.
Holds scores (one ReviewScore per criterion), written feedback,
and an overall recommendation.

ConflictOfInterest: a reviewer declares they shouldn't review
a particular submission.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from conference.models import Conference
from submissions.models import Submission


class ReviewCriterion(models.Model):
    """A single scoring criterion in the rubric, e.g. 'Originality 1-5'."""

    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name='review_criteria',
    )
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True,
        help_text='Short hint shown under the slider.')
    weight = models.PositiveIntegerField(
        default=1,
        help_text='Used when calculating overall scores. 1 = equal weight.',
    )
    min_score = models.PositiveIntegerField(default=1)
    max_score = models.PositiveIntegerField(default=5)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ('conference', 'name')

    def __str__(self):
        return f"{self.name} ({self.conference.name})"


class Review(models.Model):
    """One reviewer assigned to one submission."""

    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_RECUSED = 'recused'
    STATUS_CHOICES = [
        (STATUS_PENDING,     'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED,   'Completed'),
        (STATUS_RECUSED,     'Recused'),
    ]

    REC_STRONG_ACCEPT = 'strong_accept'
    REC_ACCEPT = 'accept'
    REC_WEAK_ACCEPT = 'weak_accept'
    REC_BORDERLINE = 'borderline'
    REC_WEAK_REJECT = 'weak_reject'
    REC_REJECT = 'reject'
    REC_CHOICES = [
        (REC_STRONG_ACCEPT, 'Strong Accept'),
        (REC_ACCEPT,        'Accept'),
        (REC_WEAK_ACCEPT,   'Weak Accept'),
        (REC_BORDERLINE,    'Borderline'),
        (REC_WEAK_REJECT,   'Weak Reject'),
        (REC_REJECT,        'Reject'),
    ]

    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='reviews',
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews_assigned',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default=STATUS_PENDING)

    # Written feedback
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    additional_comments = models.TextField(blank=True)

    recommendation = models.CharField(max_length=20, choices=REC_CHOICES,
                                       blank=True)

    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_at']
        unique_together = ('submission', 'reviewer')

    def __str__(self):
        return f"{self.reviewer.username} → {self.submission.title}"

    @property
    def average_score(self):
        """Weighted average across all criterion scores."""
        scores = self.scores.select_related('criterion')
        if not scores.exists():
            return None
        total = 0
        weight_sum = 0
        for s in scores:
            total += s.value * s.criterion.weight
            weight_sum += s.criterion.weight
        return round(total / weight_sum, 2) if weight_sum else None

    @property
    def is_completed(self):
        return self.status == self.STATUS_COMPLETED

    @property
    def is_recused(self):
        return self.status == self.STATUS_RECUSED


class ReviewScore(models.Model):
    """One reviewer's score for one criterion."""
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='scores',
    )
    criterion = models.ForeignKey(
        ReviewCriterion, on_delete=models.CASCADE,
    )
    value = models.PositiveIntegerField()

    class Meta:
        unique_together = ('review', 'criterion')

    def __str__(self):
        return f"{self.criterion.name}: {self.value}"


class ConflictOfInterest(models.Model):
    """A reviewer declaring they have a conflict on a submission."""

    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='conflicts',
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='conflicts_declared',
    )
    reason = models.TextField(
        help_text='Brief reason — e.g. co-author, colleague, competitor.',
    )
    declared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('submission', 'reviewer')

    def __str__(self):
        return f"COI: {self.reviewer.username} on {self.submission.title}"