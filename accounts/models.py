"""
Models for the 'accounts' app.

Django provides a built-in User model (username, email, password).
We extend it with a Profile that stores the role and organisation,
without having to replace the whole User system.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """
    One Profile per User. Holds the conference-specific info:
    role and organisation/affiliation.
    """

    # Role choices. The first value is what's stored in the DB,
    # the second is what humans see.
    ROLE_ORGANISER = 'organiser'
    ROLE_AUTHOR = 'author'
    ROLE_REVIEWER = 'reviewer'
    ROLE_PARTICIPANT = 'participant'

    ROLE_CHOICES = [
        (ROLE_ORGANISER, 'Organiser'),
        (ROLE_AUTHOR, 'Author'),
        (ROLE_REVIEWER, 'Reviewer'),
        (ROLE_PARTICIPANT, 'Participant'),
    ]

    # OneToOneField means: exactly one Profile per User.
    # If the User is deleted, the Profile is deleted too.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_PARTICIPANT,
    )

    affiliation = models.CharField(
        max_length=200,
        blank=True,
        help_text="Organisation or university the user belongs to.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    # Helper methods that make role checks read nicely in views/templates.
    def is_organiser(self):
        return self.role == self.ROLE_ORGANISER

    def is_author(self):
        return self.role == self.ROLE_AUTHOR

    def is_reviewer(self):
        return self.role == self.ROLE_REVIEWER

    def is_participant(self):
        return self.role == self.ROLE_PARTICIPANT


# ----------------------------------------------------------------------
# Signals: automatically create/save a Profile whenever a User is created.
# This guarantees every User has a Profile — no orphaned accounts.
# ----------------------------------------------------------------------

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """When a new User is created, create a Profile for them."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """When a User is saved, also save their Profile."""
    # Defensive: in case a Profile somehow doesn't exist yet.
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()