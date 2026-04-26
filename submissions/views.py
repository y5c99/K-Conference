"""
Views for the 'submissions' app.

Authors:
- list their own submissions
- create a new submission
- view / edit their own
- upload manuscript files
- withdraw

Organisers (own conferences):
- view all submissions
- view individual submissions
- override deadlines / status

Reviewers:
- (handled in Phase 5)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.utils import timezone
from django.db.models import Q

from accounts.models import Profile
from conference.models import Conference
from .models import Submission, SubmissionFile
from .forms import SubmissionForm, SubmissionFileForm


# ---------- Permission helpers ----------

def _can_view_submission(user, submission):
    """Authors see their own; organisers see those for their conferences;
    reviewers see those they're assigned to."""
    if not user.is_authenticated:
        return False
    if user == submission.author:
        return True
    if user == submission.conference.organiser:
        return True
    if user.is_staff:
        return True
    # Phase 5: assigned reviewers can also view
    from reviews.models import Review
    if Review.objects.filter(
        submission=submission, reviewer=user,
    ).exclude(status=Review.STATUS_RECUSED).exists():
        return True
    return False


def _can_edit_submission(user, submission):
    """Only the author can edit, and only while editable."""
    return user == submission.author and submission.is_editable_by_author


# ---------- Author: list their submissions ----------

@login_required
def my_submissions(request):
    """The 'My Submissions' screen."""
    submissions = Submission.objects.filter(
        author=request.user
    ).select_related('conference', 'track')

    # Sidebar variant depending on role
    role = request.user.profile.role

    return render(request, 'submissions/my_submissions.html', {
        'submissions': submissions,
        'role': role,
    })


# ---------- Author: create new submission ----------

@login_required
def submission_create(request):
    """
    Choose which conference to submit to, then fill in the paper details.
    """
    # Only authors can submit
    if request.user.profile.role != Profile.ROLE_AUTHOR:
        messages.error(request, 'Only authors can submit papers.')
        return redirect('accounts:dashboard')

    # Find conferences accepting submissions
    open_conferences = Conference.objects.filter(
        status=Conference.STATUS_OPEN,
        submission_deadline__gt=timezone.now(),
    )

    if not open_conferences.exists():
        return render(request, 'submissions/no_open_conferences.html')

    # If there's only one, auto-pick it. Otherwise let the author choose.
    conference_id = request.GET.get('conference') or request.POST.get('conference')
    conference = None
    if conference_id:
        conference = open_conferences.filter(pk=conference_id).first()
    if not conference and open_conferences.count() == 1:
        conference = open_conferences.first()

    if not conference:
        return render(request, 'submissions/choose_conference.html', {
            'conferences': open_conferences,
        })

    if request.method == 'POST':
        form = SubmissionForm(request.POST, conference=conference)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.conference = conference
            submission.author = request.user
            submission.status = Submission.STATUS_DRAFT
            submission.save()
            submission.assign_id_code()
            submission.save(update_fields=['submission_id_code'])

            messages.success(
                request,
                f'Draft saved. ID: {submission.submission_id_code}. '
                f'Now upload your manuscript.'
            )
            return redirect('submissions:upload_file', pk=submission.pk)
    else:
        form = SubmissionForm(conference=conference)

    return render(request, 'submissions/submission_form.html', {
        'form': form,
        'conference': conference,
        'mode': 'create',
    })


# ---------- Author: edit existing draft ----------

@login_required
def submission_edit(request, pk):
    submission = get_object_or_404(Submission, pk=pk)

    if not _can_edit_submission(request.user, submission):
        messages.error(request, 'You cannot edit this submission.')
        return redirect('submissions:detail', pk=pk)

    if request.method == 'POST':
        form = SubmissionForm(request.POST, instance=submission,
                              conference=submission.conference)
        if form.is_valid():
            form.save()
            messages.success(request, 'Submission updated.')
            return redirect('submissions:detail', pk=submission.pk)
    else:
        form = SubmissionForm(instance=submission,
                              conference=submission.conference)

    return render(request, 'submissions/submission_form.html', {
        'form': form,
        'conference': submission.conference,
        'submission': submission,
        'mode': 'edit',
    })


# ---------- Author: detail view ----------

@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(Submission, pk=pk)

    if not _can_view_submission(request.user, submission):
        return HttpResponseForbidden()

    return render(request, 'submissions/submission_detail.html', {
        'submission': submission,
        'files': submission.files.all(),
        'is_author': request.user == submission.author,
        'is_organiser': request.user == submission.conference.organiser,
    })


# ---------- Author: upload / replace manuscript ----------

@login_required
def submission_upload_file(request, pk):
    submission = get_object_or_404(Submission, pk=pk)

    if not _can_edit_submission(request.user, submission):
        messages.error(request, 'This submission is locked.')
        return redirect('submissions:detail', pk=pk)

    if request.method == 'POST':
        form = SubmissionFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.cleaned_data['file']
            # Next version number
            next_version = (submission.files.count() or 0) + 1
            SubmissionFile.objects.create(
                submission=submission,
                file=uploaded,
                version=next_version,
                uploaded_by=request.user,
            )
            messages.success(request,
                f'Manuscript uploaded (v{next_version}).')
            return redirect('submissions:detail', pk=submission.pk)
    else:
        form = SubmissionFileForm()

    return render(request, 'submissions/upload_file.html', {
        'form': form,
        'submission': submission,
    })


# ---------- Author: submit (move from draft → submitted) ----------

@login_required
def submission_finalise(request, pk):
    submission = get_object_or_404(Submission, pk=pk)

    if request.user != submission.author:
        return HttpResponseForbidden()

    if submission.is_locked:
        messages.error(request, 'The submission deadline has passed.')
        return redirect('submissions:detail', pk=pk)

    if not submission.files.exists():
        messages.error(request,
            'You must upload a manuscript file before submitting.')
        return redirect('submissions:upload_file', pk=pk)

    if request.method == 'POST':
        submission.status = Submission.STATUS_SUBMITTED
        submission.submitted_at = timezone.now()
        submission.save(update_fields=['status', 'submitted_at'])
        messages.success(request,
            f'"{submission.title}" submitted to {submission.conference.name}.')
        return redirect('submissions:detail', pk=pk)

    return render(request, 'submissions/finalise_confirm.html', {
        'submission': submission,
    })


# ---------- Author: withdraw ----------

@login_required
def submission_withdraw(request, pk):
    submission = get_object_or_404(Submission, pk=pk)

    if request.user != submission.author:
        return HttpResponseForbidden()

    if submission.status in (Submission.STATUS_ACCEPTED,
                             Submission.STATUS_REJECTED):
        messages.error(request, 'Cannot withdraw — decision already made.')
        return redirect('submissions:detail', pk=pk)

    if request.method == 'POST':
        submission.status = Submission.STATUS_WITHDRAWN
        submission.save(update_fields=['status'])
        messages.info(request, 'Submission withdrawn.')
        return redirect('submissions:my_submissions')

    return render(request, 'submissions/withdraw_confirm.html', {
        'submission': submission,
    })


# ---------- Secure file download ----------

@login_required
def download_file(request, file_pk):
    """
    Send the manuscript file to the user — but only if they're allowed.
    Files are stored under MEDIA_ROOT but we don't expose direct URLs;
    we serve them via this view to enforce permissions.
    """
    sub_file = get_object_or_404(SubmissionFile, pk=file_pk)

    if not _can_view_submission(request.user, sub_file.submission):
        return HttpResponseForbidden()

    try:
        return FileResponse(
            sub_file.file.open('rb'),
            as_attachment=True,
            filename=sub_file.filename,
        )
    except FileNotFoundError:
        raise Http404('File not found on server.')


# ---------- Organiser: view all submissions for a conference ----------

@login_required
def organiser_submission_list(request, conference_pk):
    conference = get_object_or_404(Conference, pk=conference_pk)

    if request.user != conference.organiser and not request.user.is_staff:
        return HttpResponseForbidden()

    status_filter = request.GET.get('status', '')
    submissions = conference.submissions.select_related('author', 'track')
    if status_filter:
        submissions = submissions.filter(status=status_filter)

    return render(request, 'submissions/organiser_list.html', {
        'conference': conference,
        'submissions': submissions,
        'status_filter': status_filter,
        'status_choices': Submission.STATUS_CHOICES,
    })
# ---------- Organiser: decisions dashboard + per-paper decision ----------

@login_required
def decisions_dashboard(request, conference_pk):
    """
    Bulk view: all submissions with their average review score
    and current status. From here, click any row to make a decision.
    """
    from conference.models import Conference

    conference = get_object_or_404(Conference, pk=conference_pk)
    if request.user != conference.organiser and not request.user.is_staff:
        return HttpResponseForbidden()

    submissions = conference.submissions.select_related(
        'author', 'track'
    ).prefetch_related('reviews__scores__criterion')

    # Annotate each submission with stats
    rows = []
    for s in submissions:
        completed_reviews = [r for r in s.reviews.all() if r.is_completed]
        avg = None
        if completed_reviews:
            scores = [r.average_score for r in completed_reviews if r.average_score]
            if scores:
                avg = round(sum(scores) / len(scores), 2)

        rows.append({
            'submission': s,
            'reviews_total': s.reviews.count(),
            'reviews_completed': len(completed_reviews),
            'average_score': avg,
        })

    # Counts for the stats row
    counts = {
        'total': submissions.count(),
        'submitted': submissions.filter(
            status=Submission.STATUS_SUBMITTED).count(),
        'under_review': submissions.filter(
            status=Submission.STATUS_UNDER_REVIEW).count(),
        'accepted': submissions.filter(
            status=Submission.STATUS_ACCEPTED).count(),
        'rejected': submissions.filter(
            status=Submission.STATUS_REJECTED).count(),
    }

    return render(request, 'submissions/decisions_dashboard.html', {
        'conference': conference,
        'rows': rows,
        'counts': counts,
    })


@login_required
def make_decision(request, pk):
    """The organiser's decision page for a single submission."""
    from .forms import DecisionForm
    from core.models import AuditLog

    submission = get_object_or_404(Submission, pk=pk)
    if request.user != submission.conference.organiser and not request.user.is_staff:
        return HttpResponseForbidden()

    completed_reviews = submission.reviews.filter(
        status='completed',
    ).select_related('reviewer').prefetch_related('scores__criterion')

    if request.method == 'POST':
        form = DecisionForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['decision']
            notes = form.cleaned_data['notes']

            # Track if this is overriding an earlier decision
            is_override = submission.status in (
                Submission.STATUS_ACCEPTED, Submission.STATUS_REJECTED
            )

            old_status = submission.status
            submission.status = new_status
            submission.decision_at = timezone.now()
            submission.decision_notes = notes
            submission.save(update_fields=['status', 'decision_at', 'decision_notes'])

            # Audit log
            AuditLog.log(
                conference=submission.conference,
                actor=request.user,
                action=(AuditLog.ACTION_DECISION_OVERRIDE if is_override
                        else AuditLog.ACTION_DECISION_MADE),
                target=f'Submission {submission.submission_id_code or submission.pk}',
                notes=f'{old_status} → {new_status}'
                      + (f' | {notes}' if notes else ''),
            )

            messages.success(request,
                f'Decision recorded: {submission.get_status_display()}')
            return redirect('submissions:decisions_dashboard',
                            conference_pk=submission.conference.pk)
    else:
        # Pre-select current status if it's already a decision
        initial = {}
        if submission.status in ('accepted', 'rejected', 'under_review'):
            initial['decision'] = submission.status
        if submission.decision_notes:
            initial['notes'] = submission.decision_notes
        form = DecisionForm(initial=initial)

    # Compute summary score
    avg_score = None
    if completed_reviews.exists():
        scores = [r.average_score for r in completed_reviews if r.average_score]
        if scores:
            avg_score = round(sum(scores) / len(scores), 2)

    return render(request, 'submissions/make_decision.html', {
        'submission': submission,
        'reviews': completed_reviews,
        'avg_score': avg_score,
        'form': form,
    })