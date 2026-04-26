"""
Core app models.

Announcement: organiser broadcasts to participants/authors/reviewers.
FAQ: question & answer pairs per conference.
AuditLog: tracks critical organiser actions for transparency.
"""

from django.db import models
from django.contrib.auth.models import User
from conference.models import Conference


class Announcement(models.Model):
    """A broadcast message shown to participants of a conference."""

    AUDIENCE_ALL = 'all'
    AUDIENCE_AUTHORS = 'authors'
    AUDIENCE_REVIEWERS = 'reviewers'
    AUDIENCE_PARTICIPANTS = 'participants'
    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL,          'Everyone'),
        (AUDIENCE_AUTHORS,      'Authors only'),
        (AUDIENCE_REVIEWERS,    'Reviewers only'),
        (AUDIENCE_PARTICIPANTS, 'Participants only'),
    ]

    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name='announcements',
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES,
                                 default=AUDIENCE_ALL)
    is_pinned = models.BooleanField(
        default=False, help_text='Pinned announcements appear first.',
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='announcements_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """Question + answer pairs per conference."""

    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name='faqs',
    )
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question[:60]


class AuditLog(models.Model):
    """Tracks critical actions for transparency and accountability."""

    ACTION_DEADLINE_OVERRIDE = 'deadline_override'
    ACTION_DECISION_MADE     = 'decision_made'
    ACTION_DECISION_OVERRIDE = 'decision_override'
    ACTION_STATUS_CHANGE     = 'status_change'
    ACTION_REVIEW_REOPEN     = 'review_reopen'
    ACTION_SUBMISSION_UNLOCK = 'submission_unlock'
    ACTION_OTHER             = 'other'

    ACTION_CHOICES = [
        (ACTION_DEADLINE_OVERRIDE, 'Deadline override'),
        (ACTION_DECISION_MADE,     'Decision made'),
        (ACTION_DECISION_OVERRIDE, 'Decision overridden'),
        (ACTION_STATUS_CHANGE,     'Status change'),
        (ACTION_REVIEW_REOPEN,     'Review reopened'),
        (ACTION_SUBMISSION_UNLOCK, 'Submission unlocked'),
        (ACTION_OTHER,             'Other'),
    ]

    conference = models.ForeignKey(
        Conference, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs',
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='audit_actions',
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target = models.CharField(
        max_length=200, blank=True,
        help_text='What was acted on (e.g. "Submission #42").',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} by {self.actor} at {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def log(cls, *, conference=None, actor=None, action,
            target='', notes=''):
        """Convenience factory used everywhere in the app."""
        return cls.objects.create(
            conference=conference,
            actor=actor,
            action=action,
            target=target,
            notes=notes,
        )