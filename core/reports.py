"""
Helpers for building report data.
Each function takes a Conference and returns a dict the template can render.
"""

from collections import OrderedDict, Counter
from datetime import timedelta

from django.db.models import Count, Avg
from django.utils import timezone

from conference.models import Registration
from submissions.models import Submission
from reviews.models import Review, ReviewScore


def registration_stats(conference):
    """Total + per-day registrations. Returns a dict for the template."""
    regs = conference.registrations.all()
    total = regs.count()
    confirmed = regs.filter(status=Registration.STATUS_CONFIRMED).count()
    waitlist = regs.filter(status=Registration.STATUS_WAITLIST).count()

    # --- daily breakdown for last 30 days ---
    today = timezone.localdate()
    start = today - timedelta(days=29)
    by_day = OrderedDict()
    for i in range(30):
        d = start + timedelta(days=i)
        by_day[d] = 0

    for r in regs.filter(registered_at__date__gte=start):
        d = r.registered_at.date()
        by_day[d] = by_day.get(d, 0) + 1

    max_day = max(by_day.values()) if by_day.values() else 1
    series = [
        {'date': d, 'count': c, 'percent': round((c / max_day) * 100) if max_day else 0}
        for d, c in by_day.items()
    ]

    return {
        'total': total,
        'confirmed': confirmed,
        'waitlist': waitlist,
        'capacity': conference.capacity,
        'capacity_pct': round((confirmed / conference.capacity) * 100)
                        if conference.capacity else None,
        'series': series,
    }


def submission_stats(conference):
    """Submission counts by status + by track."""
    submissions = conference.submissions.all()
    total = submissions.count()

    by_status = {
        s: submissions.filter(status=s_value).count()
        for s, s_value in [
            ('draft',        Submission.STATUS_DRAFT),
            ('submitted',    Submission.STATUS_SUBMITTED),
            ('under_review', Submission.STATUS_UNDER_REVIEW),
            ('accepted',     Submission.STATUS_ACCEPTED),
            ('rejected',     Submission.STATUS_REJECTED),
            ('withdrawn',    Submission.STATUS_WITHDRAWN),
        ]
    }

    decided = by_status['accepted'] + by_status['rejected']
    acceptance_rate = (
        round((by_status['accepted'] / decided) * 100, 1) if decided else None
    )

    # By track
    by_track = []
    for track in conference.tracks.all():
        track_subs = submissions.filter(track=track)
        accepted = track_subs.filter(status=Submission.STATUS_ACCEPTED).count()
        rejected = track_subs.filter(status=Submission.STATUS_REJECTED).count()
        decided_count = accepted + rejected
        by_track.append({
            'name': track.name,
            'total': track_subs.count(),
            'accepted': accepted,
            'rejected': rejected,
            'acceptance_rate': (round((accepted / decided_count) * 100, 1)
                                if decided_count else None),
        })

    # Bar chart of statuses
    max_status = max(by_status.values()) if by_status.values() else 1
    status_chart = [
        {'label': k.replace('_', ' ').title(), 'count': v,
         'percent': round((v / max_status) * 100) if max_status else 0,
         'key': k}
        for k, v in by_status.items() if v > 0
    ]

    return {
        'total': total,
        'by_status': by_status,
        'acceptance_rate': acceptance_rate,
        'by_track': by_track,
        'status_chart': status_chart,
    }


def review_stats(conference):
    """How are the reviews going?"""
    reviews = Review.objects.filter(submission__conference=conference)
    total = reviews.count()

    pending = reviews.filter(status=Review.STATUS_PENDING).count()
    in_progress = reviews.filter(status=Review.STATUS_IN_PROGRESS).count()
    completed = reviews.filter(status=Review.STATUS_COMPLETED).count()
    recused = reviews.filter(status=Review.STATUS_RECUSED).count()

    completion_pct = round((completed / total) * 100, 1) if total else 0

    # Recommendation distribution (from completed reviews)
    rec_counts = (reviews.filter(status=Review.STATUS_COMPLETED)
                  .exclude(recommendation='')
                  .values('recommendation')
                  .annotate(n=Count('id')))
    rec_lookup = dict(Review.REC_CHOICES)
    rec_chart = []
    rec_max = max([r['n'] for r in rec_counts], default=1)
    for r in rec_counts:
        rec_chart.append({
            'label': rec_lookup.get(r['recommendation'], r['recommendation']),
            'count': r['n'],
            'percent': round((r['n'] / rec_max) * 100) if rec_max else 0,
        })

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'recused': recused,
        'completion_pct': completion_pct,
        'rec_chart': rec_chart,
    }


def score_distribution(conference):
    """Histogram of scores given across all completed reviews."""
    scores = ReviewScore.objects.filter(
        review__submission__conference=conference,
        review__status=Review.STATUS_COMPLETED,
    ).select_related('criterion')

    counter = Counter(s.value for s in scores)
    total = sum(counter.values())
    if not total:
        return {'has_data': False, 'bars': [], 'total': 0, 'avg': None}

    max_count = max(counter.values())
    bars = []
    # Show bars 1..5 (or whatever range). We'll detect the actual range:
    if scores:
        min_v = min(s.criterion.min_score for s in scores)
        max_v = max(s.criterion.max_score for s in scores)
    else:
        min_v, max_v = 1, 5

    for v in range(min_v, max_v + 1):
        c = counter.get(v, 0)
        bars.append({
            'value': v,
            'count': c,
            'percent': round((c / max_count) * 100) if max_count else 0,
        })

    avg = round(sum(s.value for s in scores) / total, 2)

    return {
        'has_data': True,
        'bars': bars,
        'total': total,
        'avg': avg,
    }