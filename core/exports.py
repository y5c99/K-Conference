"""CSV export helpers. Each function returns a Django HttpResponse."""

import csv
from django.http import HttpResponse


def _csv_response(filename):
    """Make a CSV-typed HttpResponse with the right Content-Disposition."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_participants(conference):
    """Confirmed + waitlisted registrations."""
    response = _csv_response(f'{conference.short_name or "conference"}_participants.csv')
    writer = csv.writer(response)
    writer.writerow([
        'Conference', 'Username', 'Full name', 'Email',
        'Affiliation', 'Status', 'Registered At', 'Accessibility Needs',
    ])

    regs = conference.registrations.select_related('user', 'user__profile')
    for r in regs:
        u = r.user
        writer.writerow([
            conference.name,
            u.username,
            u.get_full_name(),
            u.email,
            getattr(u.profile, 'affiliation', ''),
            r.get_status_display(),
            r.registered_at.strftime('%Y-%m-%d %H:%M'),
            r.accessibility_needs,
        ])
    return response


def export_submissions(conference):
    """All submissions with key metadata."""
    response = _csv_response(f'{conference.short_name or "conference"}_submissions.csv')
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Author', 'Author Email', 'Track',
        'Status', 'Submitted At', 'Decision At', 'Decision Notes',
        'Reviews Total', 'Reviews Completed', 'Avg Score',
    ])

    for s in conference.submissions.select_related('author', 'track').all():
        completed = [r for r in s.reviews.all() if r.status == 'completed']
        avg = None
        if completed:
            scores = [r.average_score for r in completed if r.average_score]
            if scores:
                avg = round(sum(scores) / len(scores), 2)

        writer.writerow([
            s.submission_id_code or s.pk,
            s.title,
            s.author.get_full_name() or s.author.username,
            s.author.email,
            s.track.name if s.track else '',
            s.get_status_display(),
            s.submitted_at.strftime('%Y-%m-%d %H:%M') if s.submitted_at else '',
            s.decision_at.strftime('%Y-%m-%d %H:%M') if s.decision_at else '',
            s.decision_notes,
            s.reviews.count(),
            len(completed),
            avg if avg is not None else '',
        ])
    return response


def export_reviews(conference):
    """Every review (pending, completed, recused) with scores per criterion."""
    response = _csv_response(f'{conference.short_name or "conference"}_reviews.csv')
    writer = csv.writer(response)

    # Build dynamic header (one column per criterion)
    criteria = list(conference.review_criteria.all())
    header = [
        'Submission ID', 'Submission Title',
        'Reviewer', 'Reviewer Email',
        'Status', 'Recommendation',
        'Avg Score', 'Assigned At', 'Completed At',
    ]
    for c in criteria:
        header.append(f'Score: {c.name}')
    header += ['Strengths', 'Weaknesses', 'Additional Comments']
    writer.writerow(header)

    from reviews.models import Review
    reviews = (Review.objects
               .filter(submission__conference=conference)
               .select_related('reviewer', 'submission')
               .prefetch_related('scores__criterion'))

    for r in reviews:
        score_map = {s.criterion_id: s.value for s in r.scores.all()}
        row = [
            r.submission.submission_id_code or r.submission.pk,
            r.submission.title,
            r.reviewer.get_full_name() or r.reviewer.username,
            r.reviewer.email,
            r.get_status_display(),
            r.get_recommendation_display() if r.recommendation else '',
            r.average_score if r.average_score is not None else '',
            r.assigned_at.strftime('%Y-%m-%d %H:%M'),
            r.completed_at.strftime('%Y-%m-%d %H:%M') if r.completed_at else '',
        ]
        for c in criteria:
            row.append(score_map.get(c.id, ''))
        row += [r.strengths, r.weaknesses, r.additional_comments]
        writer.writerow(row)
    return response


def export_decisions(conference):
    """Compact decision list: accepted/rejected/under_review."""
    response = _csv_response(f'{conference.short_name or "conference"}_decisions.csv')
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Author', 'Track',
        'Decision', 'Decision At', 'Decision Notes', 'Avg Score',
    ])

    for s in conference.submissions.exclude(status='draft').select_related('author', 'track'):
        completed = [r for r in s.reviews.all() if r.status == 'completed']
        avg = None
        if completed:
            scores = [r.average_score for r in completed if r.average_score]
            if scores:
                avg = round(sum(scores) / len(scores), 2)

        writer.writerow([
            s.submission_id_code or s.pk,
            s.title,
            s.author.get_full_name() or s.author.username,
            s.track.name if s.track else '',
            s.get_status_display(),
            s.decision_at.strftime('%Y-%m-%d %H:%M') if s.decision_at else '',
            s.decision_notes,
            avg if avg is not None else '',
        ])
    return response