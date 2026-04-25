"""
Models for the 'submissions' app.

A Submission is one paper an author submits to a conference.
A SubmissionFile is a versioned upload of the manuscript.
This way authors can re-upload before the deadline,
and we keep a full history.
"""

import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from conference.models import Conference, Track


def manuscript_upload_path(instance, filename):
    """
    Decide where uploaded manuscript PDFs go on disk.
    Path: media/manuscripts/conference_<id>/submission_<id>/v<N>_<filename>
    """
    submission = instance.submission
    conference_id = submission.conference_id
    submission_id = submission.id or 'new'
    version = instance.version
    safe_name = filename.replace(' ', '_')
    return f'manuscripts/conference_{conference_id}/submission_{submission_id}/v{version}_{safe_name}'


class Submission(models.Model):
    """One paper submitted by an author to a conference."""

    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_WITHDRAWN = 'withdrawn'

    STATUS_CHOICES = [
        (STATUS_DRAFT,        'Draft'),
        (STATUS_SUBMITTED,    'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_ACCEPTED,     'Accepted'),
        (STATUS_REJECTED,     'Rejected'),
        (STATUS_WITHDRAWN,    'Withdrawn'),
    ]

    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name='submissions',
    )
    track = models.ForeignKey(
        Track, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submissions',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='submissions',
    )

    title = models.CharField(max_length=300)
    abstract = models.TextField(
        help_text='Short summary of the paper (max 300 words recommended).',
    )
    keywords = models.CharField(
        max_length=300, blank=True,
        help_text='Comma-separated. e.g. "machine learning, healthcare, privacy".',
    )

    # Co-authors as plain text. (Real systems would link to Users — keeping
    # it simple for the assignment.)
    co_authors = models.TextField(
        blank=True,
        help_text='One per line: full name, email, affiliation.',
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT,
    )

    submission_id_code = models.CharField(
        max_length=30, blank=True,
        help_text='Public ID shown to authors and reviewers, e.g. SUB-2026-0042.',
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    decision_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.author.username})"

    # ---- Helpful properties / methods ----

    @property
    def is_locked(self):
        """A submission is locked once the conference deadline passes."""
        return self.conference.submission_deadline_passed

    @property
    def is_editable_by_author(self):
        """Can the author still edit?"""
        if self.status in (self.STATUS_ACCEPTED, self.STATUS_REJECTED, self.STATUS_WITHDRAWN):
            return False
        return not self.is_locked

    @property
    def latest_file(self):
        """Most recent uploaded version, or None."""
        return self.files.order_by('-version').first()

    @property
    def keyword_list(self):
        """Keywords as a clean Python list, no empty strings."""
        return [k.strip() for k in self.keywords.split(',') if k.strip()]

    def assign_id_code(self):
        """Build the public ID like SUB-2026-0042 from the PK."""
        year = self.conference.start_date.year
        self.submission_id_code = f'SUB-{year}-{self.pk:04d}'


class SubmissionFile(models.Model):
    """A versioned manuscript upload."""

    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='files',
    )
    file = models.FileField(upload_to=manuscript_upload_path)
    version = models.PositiveIntegerField(default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files',
    )

    class Meta:
        ordering = ['-version']
        unique_together = ('submission', 'version')

    def __str__(self):
        return f"{self.submission.title} v{self.version}"

    @property
    def filename(self):
        """Just the filename, no path."""
        return os.path.basename(self.file.name)