"""
Views for the conference app:
- Public list / detail
- Organiser create/edit/delete (conferences, tracks, sessions)
- Participant registration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from accounts.models import Profile
from .models import Conference, Track, Session, Registration
from .forms import ConferenceForm, TrackForm, SessionForm, RegistrationForm


# ---------- Permission helpers ----------

def _is_organiser(user):
    return (user.is_authenticated and
            hasattr(user, 'profile') and
            user.profile.role == Profile.ROLE_ORGANISER)


def _user_owns_conference(user, conference):
    """Organiser must own this conference (or be staff)."""
    return user == conference.organiser or user.is_staff


# ---------- Public listings ----------

def conference_list(request):
    """Anyone can browse upcoming conferences."""
    conferences = Conference.objects.exclude(status=Conference.STATUS_DRAFT)
    return render(request, 'conference/conference_list.html',
                  {'conferences': conferences})


def conference_detail(request, pk):
    """Public detail page for a conference."""
    conference = get_object_or_404(Conference, pk=pk)

    # Hide drafts from non-owners.
    if conference.status == Conference.STATUS_DRAFT:
        if not request.user.is_authenticated or \
           not _user_owns_conference(request.user, conference):
            return HttpResponseForbidden()

    is_registered = False
    if request.user.is_authenticated:
        is_registered = Registration.objects.filter(
            conference=conference, user=request.user,
            status=Registration.STATUS_CONFIRMED,
        ).exists()

    return render(request, 'conference/conference_detail.html', {
        'conference': conference,
        'tracks': conference.tracks.all(),
        'sessions': conference.sessions.all(),
        'is_registered': is_registered,
    })


# ---------- Organiser: create / edit / delete conference ----------

@login_required
def conference_create(request):
    if not _is_organiser(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ConferenceForm(request.POST)
        if form.is_valid():
            conf = form.save(commit=False)
            conf.organiser = request.user
            conf.save()
            messages.success(request, f'Conference "{conf.name}" created.')
            return redirect('conference:detail', pk=conf.pk)
    else:
        form = ConferenceForm()

    return render(request, 'conference/conference_form.html', {
        'form': form, 'mode': 'create',
    })


@login_required
def conference_edit(request, pk):
    conference = get_object_or_404(Conference, pk=pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ConferenceForm(request.POST, instance=conference)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conference updated.')
            return redirect('conference:detail', pk=conference.pk)
    else:
        form = ConferenceForm(instance=conference)

    return render(request, 'conference/conference_form.html', {
        'form': form, 'mode': 'edit', 'conference': conference,
    })


@login_required
def conference_delete(request, pk):
    conference = get_object_or_404(Conference, pk=pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        conference.delete()
        messages.success(request, 'Conference deleted.')
        return redirect('conference:list')

    return render(request, 'conference/conference_confirm_delete.html',
                  {'conference': conference})


# ---------- Tracks ----------

@login_required
def track_create(request, conference_pk):
    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = TrackForm(request.POST)
        if form.is_valid():
            track = form.save(commit=False)
            track.conference = conference
            track.save()
            messages.success(request, f'Track "{track.name}" added.')
            return redirect('conference:detail', pk=conference.pk)
    else:
        form = TrackForm()

    return render(request, 'conference/track_form.html', {
        'form': form, 'conference': conference,
    })


@login_required
def track_delete(request, pk):
    track = get_object_or_404(Track, pk=pk)
    if not _user_owns_conference(request.user, track.conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        conf_pk = track.conference.pk
        track.delete()
        messages.success(request, 'Track deleted.')
        return redirect('conference:detail', pk=conf_pk)

    return render(request, 'conference/track_confirm_delete.html',
                  {'track': track})


# ---------- Sessions ----------

@login_required
def session_create(request, conference_pk):
    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = SessionForm(request.POST, conference=conference)
        if form.is_valid():
            session = form.save(commit=False)
            session.conference = conference
            session.save()
            messages.success(request, f'Session "{session.title}" added.')
            return redirect('conference:detail', pk=conference.pk)
    else:
        form = SessionForm(conference=conference)

    return render(request, 'conference/session_form.html', {
        'form': form, 'conference': conference,
    })


@login_required
def session_delete(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if not _user_owns_conference(request.user, session.conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        conf_pk = session.conference.pk
        session.delete()
        messages.success(request, 'Session deleted.')
        return redirect('conference:detail', pk=conf_pk)

    return render(request, 'conference/session_confirm_delete.html',
                  {'session': session})


# ---------- Participant: register / unregister ----------

@login_required
def register_for_conference(request, pk):
    conference = get_object_or_404(Conference, pk=pk)

    if not conference.is_open_for_registration:
        messages.error(request, 'Registration is not open for this conference.')
        return redirect('conference:detail', pk=conference.pk)

    # Already registered?
    existing = Registration.objects.filter(
        conference=conference, user=request.user
    ).first()
    if existing and existing.status == Registration.STATUS_CONFIRMED:
        messages.info(request, 'You are already registered.')
        return redirect('conference:detail', pk=conference.pk)

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Decide status based on capacity.
            confirmed_count = conference.registrations.filter(
                status=Registration.STATUS_CONFIRMED
            ).count()
            if conference.capacity and confirmed_count >= conference.capacity:
                status = Registration.STATUS_WAITLIST
                msg = 'Conference is full — you have been added to the waitlist.'
            else:
                status = Registration.STATUS_CONFIRMED
                msg = 'You are registered. See you there!'

            reg, _ = Registration.objects.update_or_create(
                conference=conference,
                user=request.user,
                defaults={
                    'status': status,
                    'accessibility_needs': form.cleaned_data['accessibility_needs'],
                },
            )
            messages.success(request, msg)
            return redirect('conference:detail', pk=conference.pk)
    else:
        form = RegistrationForm()

    return render(request, 'conference/register_form.html', {
        'form': form, 'conference': conference,
    })


@login_required
def unregister_from_conference(request, pk):
    conference = get_object_or_404(Conference, pk=pk)
    Registration.objects.filter(
        conference=conference, user=request.user
    ).delete()
    messages.info(request, 'You have been unregistered.')
    return redirect('conference:detail', pk=conference.pk)


# ---------- Organiser: list of own conferences ----------

@login_required
def my_conferences(request):
    if not _is_organiser(request.user):
        return HttpResponseForbidden()
    conferences = Conference.objects.filter(organiser=request.user)
    return render(request, 'conference/my_conferences.html',
                  {'conferences': conferences})