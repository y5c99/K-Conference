"""
Views for the 'reviews' app.

Reviewer:
- Dashboard list of assigned papers
- Start/continue a review
- Declare conflict of interest / recuse
- View completed review

Organiser:
- Assign reviewers to a submission
- View all reviews for a submission
- Remove an assignment
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db import transaction

from accounts.models import Profile
from submissions.models import Submission
from .models import Review, ReviewCriterion, ReviewScore, ConflictOfInterest
from .forms import ReviewForm, ConflictOfInterestForm, AssignReviewerForm


# ---------- Permission helpers ----------

def _is_organiser_of(user, submission):
    return user == submission.conference.organiser or user.is_staff


def _is_assigned_reviewer(user, submission):
    return Review.objects.filter(
        submission=submission, reviewer=user,
    ).exclude(status=Review.STATUS_RECUSED).exists()


# ---------- Reviewer: list assigned papers ----------

@login_required
def my_assigned_reviews(request):
    """The 'Assigned Papers' page."""
    if request.user.profile.role != Profile.ROLE_REVIEWER:
        return HttpResponseForbidden()

    reviews = Review.objects.filter(
        reviewer=request.user,
    ).exclude(status=Review.STATUS_RECUSED).select_related(
        'submission', 'submission__conference', 'submission__track',
    )

    return render(request, 'reviews/my_assigned.html', {
        'reviews': reviews,
    })


# ---------- Reviewer: review form ----------

@login_required
def review_form(request, pk):
    """
    The big form: COI declaration + scores + written feedback + recommendation.
    Once submitted, the review is locked.
    """
    review = get_object_or_404(Review, pk=pk)

    if review.reviewer != request.user:
        return HttpResponseForbidden()

    submission = review.submission
    criteria = submission.conference.review_criteria.all()

    # If completed, redirect to the read-only view
    if review.is_completed:
        return redirect('reviews:view_review', pk=review.pk)

    # If recused, kick them out
    if review.is_recused:
        messages.info(request, 'You have recused yourself from this review.')
        return redirect('reviews:my_assigned')

    # --- existing scores (so partially-completed reviews remember sliders) ---
    existing_scores = {
        s.criterion_id: s.value
        for s in review.scores.all()
    }

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)

        # Collect score data manually
        score_data = {}
        score_errors = []
        for c in criteria:
            raw = request.POST.get(f'criterion_{c.pk}')
            if raw is None or raw == '':
                score_errors.append(c.name)
                continue
            try:
                value = int(raw)
            except (TypeError, ValueError):
                score_errors.append(c.name)
                continue
            if not (c.min_score <= value <= c.max_score):
                score_errors.append(c.name)
                continue
            score_data[c.pk] = value

        if form.is_valid() and not score_errors:
            # Save inside a transaction so it's all-or-nothing.
            with transaction.atomic():
                rev = form.save(commit=False)
                rev.status = Review.STATUS_COMPLETED
                rev.completed_at = timezone.now()
                rev.save()

                # Wipe old scores and recreate
                rev.scores.all().delete()
                for criterion_id, value in score_data.items():
                    ReviewScore.objects.create(
                        review=rev,
                        criterion_id=criterion_id,
                        value=value,
                    )

                # Bump submission status to under_review (if it was 'submitted')
                if submission.status == Submission.STATUS_SUBMITTED:
                    submission.status = Submission.STATUS_UNDER_REVIEW
                    submission.save(update_fields=['status'])

            messages.success(request, 'Review submitted successfully.')
            return redirect('reviews:view_review', pk=rev.pk)
        else:
            if score_errors:
                messages.error(
                    request,
                    f"Please provide a score for: {', '.join(score_errors)}.",
                )
    else:
        form = ReviewForm(instance=review)

    # Build slider context for the template
    sliders = []
    for c in criteria:
        sliders.append({
            'criterion': c,
            'value': existing_scores.get(c.pk, c.min_score),
            'range': list(range(c.min_score, c.max_score + 1)),
        })

    return render(request, 'reviews/review_form.html', {
        'review': review,
        'submission': submission,
        'sliders': sliders,
        'form': form,
        'mode': 'edit',
    })


# ---------- Reviewer: read-only completed review ----------

@login_required
def view_review(request, pk):
    review = get_object_or_404(Review, pk=pk)

    # Reviewer who wrote it, organiser, or staff can view
    is_owner = review.reviewer == request.user
    is_organiser = _is_organiser_of(request.user, review.submission)

    if not (is_owner or is_organiser or request.user.is_staff):
        return HttpResponseForbidden()

    return render(request, 'reviews/view_review.html', {
        'review': review,
        'submission': review.submission,
        'scores': review.scores.select_related('criterion'),
    })


# ---------- Reviewer: declare conflict of interest ----------

@login_required
def declare_conflict(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if review.reviewer != request.user:
        return HttpResponseForbidden()

    if review.is_completed:
        messages.error(request, 'Cannot recuse — review already submitted.')
        return redirect('reviews:view_review', pk=pk)

    if request.method == 'POST':
        form = ConflictOfInterestForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                ConflictOfInterest.objects.update_or_create(
                    submission=review.submission,
                    reviewer=request.user,
                    defaults={'reason': form.cleaned_data['reason']},
                )
                review.status = Review.STATUS_RECUSED
                review.save(update_fields=['status'])

            messages.info(request, 'You have recused yourself from this review.')
            return redirect('reviews:my_assigned')
    else:
        form = ConflictOfInterestForm()

    return render(request, 'reviews/declare_conflict.html', {
        'review': review,
        'form': form,
    })


# ---------- Organiser: assign a reviewer ----------

@login_required
def assign_reviewer(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)

    if not _is_organiser_of(request.user, submission):
        return HttpResponseForbidden()

    # Pool: all users with reviewer role, minus already-assigned + recused.
    assigned_ids = list(submission.reviews.values_list('reviewer_id', flat=True))
    available = User.objects.filter(
        profile__role=Profile.ROLE_REVIEWER,
    ).exclude(pk__in=assigned_ids)

    if request.method == 'POST':
        form = AssignReviewerForm(request.POST, available_reviewers=available)
        if form.is_valid():
            reviewer = form.cleaned_data['reviewer']
            Review.objects.create(
                submission=submission,
                reviewer=reviewer,
                status=Review.STATUS_PENDING,
            )
            # If the submission was 'submitted', mark under_review
            if submission.status == Submission.STATUS_SUBMITTED:
                submission.status = Submission.STATUS_UNDER_REVIEW
                submission.save(update_fields=['status'])
            messages.success(request,
                f'{reviewer.get_full_name() or reviewer.username} assigned.')
            return redirect('reviews:submission_reviews',
                            submission_pk=submission.pk)
    else:
        form = AssignReviewerForm(available_reviewers=available)

    return render(request, 'reviews/assign_reviewer.html', {
        'form': form,
        'submission': submission,
        'has_reviewers': available.exists(),
    })


# ---------- Organiser: view all reviews for a submission ----------

@login_required
def submission_reviews(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)

    if not _is_organiser_of(request.user, submission):
        return HttpResponseForbidden()

    reviews = submission.reviews.select_related('reviewer').all()

    return render(request, 'reviews/submission_reviews.html', {
        'submission': submission,
        'reviews': reviews,
        'conflicts': submission.conflicts.select_related('reviewer'),
    })


# ---------- Organiser: remove an assignment ----------

@login_required
def remove_assignment(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if not _is_organiser_of(request.user, review.submission):
        return HttpResponseForbidden()

    if review.is_completed:
        messages.error(request, 'Cannot remove a completed review.')
        return redirect('reviews:submission_reviews',
                        submission_pk=review.submission.pk)

    if request.method == 'POST':
        sub_pk = review.submission.pk
        review.delete()
        messages.info(request, 'Assignment removed.')
        return redirect('reviews:submission_reviews', submission_pk=sub_pk)

    return render(request, 'reviews/remove_assignment_confirm.html', {
        'review': review,
    })