"""
Views for the 'core' app.

Public:
- Home page
- FAQ list (per conference)

Organiser:
- Manage announcements (CRUD)
- Manage FAQs (CRUD)
- View audit log
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q

from accounts.models import Profile
from conference.models import Conference
from .models import Announcement, FAQ, AuditLog
from .forms import AnnouncementForm, FAQForm


# ---------- Permission helper ----------

def _user_owns_conference(user, conference):
    return user == conference.organiser or user.is_staff


# ---------- Home ----------

def home(request):
    return render(request, 'core/home.html')


# ---------- Announcements ----------

@login_required
def announcement_list(request, conference_pk):
    """List of announcements for a conference (organiser view, manageable)."""
    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    announcements = conference.announcements.all()
    return render(request, 'core/announcement_list.html', {
        'conference': conference,
        'announcements': announcements,
    })


@login_required
def announcement_create(request, conference_pk):
    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.conference = conference
            ann.created_by = request.user
            ann.save()
            messages.success(request, 'Announcement published.')
            return redirect('core:announcement_list', conference_pk=conference.pk)
    else:
        form = AnnouncementForm()

    return render(request, 'core/announcement_form.html', {
        'form': form, 'conference': conference, 'mode': 'create',
    })


@login_required
def announcement_edit(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if not _user_owns_conference(request.user, ann.conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=ann)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated.')
            return redirect('core:announcement_list',
                            conference_pk=ann.conference.pk)
    else:
        form = AnnouncementForm(instance=ann)

    return render(request, 'core/announcement_form.html', {
        'form': form, 'conference': ann.conference, 'mode': 'edit',
    })


@login_required
def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if not _user_owns_conference(request.user, ann.conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        conf_pk = ann.conference.pk
        ann.delete()
        messages.info(request, 'Announcement deleted.')
        return redirect('core:announcement_list', conference_pk=conf_pk)

    return render(request, 'core/announcement_confirm_delete.html',
                  {'announcement': ann})


# ---------- FAQs ----------

def faq_list(request, conference_pk):
    """Public FAQ page for a conference."""
    conference = get_object_or_404(Conference, pk=conference_pk)
    is_organiser = (request.user.is_authenticated and
                    _user_owns_conference(request.user, conference))

    faqs = conference.faqs.all()
    if not is_organiser:
        faqs = faqs.filter(is_published=True)

    return render(request, 'core/faq_list.html', {
        'conference': conference,
        'faqs': faqs,
        'is_organiser': is_organiser,
    })


@login_required
def faq_create(request, conference_pk):
    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            faq = form.save(commit=False)
            faq.conference = conference
            faq.save()
            messages.success(request, 'FAQ added.')
            return redirect('core:faq_list', conference_pk=conference.pk)
    else:
        form = FAQForm()

    return render(request, 'core/faq_form.html', {
        'form': form, 'conference': conference, 'mode': 'create',
    })


@login_required
def faq_edit(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    if not _user_owns_conference(request.user, faq.conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ updated.')
            return redirect('core:faq_list', conference_pk=faq.conference.pk)
    else:
        form = FAQForm(instance=faq)

    return render(request, 'core/faq_form.html', {
        'form': form, 'conference': faq.conference, 'mode': 'edit',
    })


@login_required
def faq_delete(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    if not _user_owns_conference(request.user, faq.conference):
        return HttpResponseForbidden()

    if request.method == 'POST':
        conf_pk = faq.conference.pk
        faq.delete()
        messages.info(request, 'FAQ deleted.')
        return redirect('core:faq_list', conference_pk=conf_pk)

    return render(request, 'core/faq_confirm_delete.html', {'faq': faq})


# ---------- Audit log ----------

@login_required
def audit_log(request, conference_pk):
    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    logs = conference.audit_logs.select_related('actor').all()

    return render(request, 'core/audit_log.html', {
        'conference': conference,
        'logs': logs,
    })

# ---------- Reports ----------

@login_required
def reports_dashboard(request, conference_pk):
    """The main reports page for a conference."""
    from .reports import (
        registration_stats, submission_stats,
        review_stats, score_distribution,
    )

    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    return render(request, 'core/reports.html', {
        'conference': conference,
        'reg':   registration_stats(conference),
        'sub':   submission_stats(conference),
        'rev':   review_stats(conference),
        'score': score_distribution(conference),
    })


# ---------- CSV downloads ----------

@login_required
def export_csv(request, conference_pk, kind):
    """Single endpoint that dispatches to the right CSV exporter."""
    from . import exports

    conference = get_object_or_404(Conference, pk=conference_pk)
    if not _user_owns_conference(request.user, conference):
        return HttpResponseForbidden()

    if kind == 'participants':
        return exports.export_participants(conference)
    if kind == 'submissions':
        return exports.export_submissions(conference)
    if kind == 'reviews':
        return exports.export_reviews(conference)
    if kind == 'decisions':
        return exports.export_decisions(conference)

    messages.error(request, 'Unknown export type.')
    return redirect('core:reports', conference_pk=conference.pk)