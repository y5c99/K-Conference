"""
Models for the 'conference' app.

A Conference is the main event (e.g. "ISCE 2026").
A Track is a topic area within a conference (e.g. "Security & Privacy").
A Session is a scheduled item (e.g. "Opening Keynote", "Paper Session 1").
A Registration is a participant's signup to attend.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Conference(models.Model):
    """The top-level event."""

    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_DRAFT,  'Draft'),
        (STATUS_OPEN,   'Open'),
        (STATUS_CLOSED, 'Closed'),
    ]

    MODE_IN_PERSON = 'in_person'
    MODE_ONLINE = 'online'
    MODE_HYBRID = 'hybrid'
    MODE_CHOICES = [
        (MODE_IN_PERSON, 'In-person'),
        (MODE_ONLINE,    'Online'),
        (MODE_HYBRID,    'Hybrid'),
    ]

    name = models.CharField(max_length=200)
    short_name = models.CharField(
        max_length=50, blank=True,
        help_text='Short tag (e.g. "ISCE 2026"). Optional.',
    )
    description = models.TextField(blank=True)

    organiser = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='conferences_organised',
    )

    start_date = models.DateField()
    end_date = models.DateField()

    location = models.CharField(
        max_length=200, blank=True,
        help_text='Venue or city. Leave blank for fully online.',
    )
    online_link = models.URLField(
        blank=True,
        help_text='Zoom/Teams link (for online or hybrid events).',
    )

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_HYBRID)

    capacity = models.PositiveIntegerField(
        default=0,
        help_text='Maximum participants. 0 = unlimited.',
    )

    submission_deadline = models.DateTimeField(
        null=True, blank=True,
        help_text='Last moment authors can submit papers.',
    )
    review_deadline = models.DateTimeField(
        null=True, blank=True,
        help_text='Last moment reviewers must submit reviews.',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    code_of_conduct = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    # ---- Helpful properties used in templates ----
    @property
    def days_until_start(self):
        """Whole days from today until the start date. Negative if past."""
        delta = self.start_date - timezone.localdate()
        return delta.days

    @property
    def is_open_for_registration(self):
        return self.status == self.STATUS_OPEN and self.start_date >= timezone.localdate()

    @property
    def participants_count(self):
        return self.registrations.filter(status=Registration.STATUS_CONFIRMED).count()

    @property
    def submission_deadline_passed(self):
        if not self.submission_deadline:
            return False
        return timezone.now() > self.submission_deadline


class Track(models.Model):
    """A topic area within a conference."""

    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name='tracks',
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        # Prevents duplicate track names within the same conference.
        unique_together = ('conference', 'name')

    def __str__(self):
        return f"{self.conference.name} — {self.name}"


class Session(models.Model):
    """A scheduled item in the programme."""

    KIND_KEYNOTE = 'keynote'
    KIND_PAPER = 'paper'
    KIND_WORKSHOP = 'workshop'
    KIND_BREAK = 'break'
    KIND_CEREMONY = 'ceremony'
    KIND_CHOICES = [
        (KIND_KEYNOTE,  'Keynote'),
        (KIND_PAPER,    'Paper Session'),
        (KIND_WORKSHOP, 'Workshop'),
        (KIND_BREAK,    'Break'),
        (KIND_CEREMONY, 'Ceremony'),
    ]

    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name='sessions',
    )
    track = models.ForeignKey(
        Track, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sessions',
    )
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_PAPER)
    speaker = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['starts_at']

    def __str__(self):
        return f"{self.title} ({self.starts_at:%d %b %H:%M})"


class Registration(models.Model):
    """A participant signing up to attend a conference."""

    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_WAITLIST = 'waitlist'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_WAITLIST,  'Waitlist'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name='registrations',
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='registrations',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    accessibility_needs = models.TextField(
        blank=True,
        help_text='Optional. Any accommodations needed.',
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registered_at']
        # A user can only register once per conference.
        unique_together = ('conference', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.conference.name}"