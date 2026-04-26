from django.contrib import admin
from .models import Review, ReviewScore, ReviewCriterion, ConflictOfInterest


class ReviewScoreInline(admin.TabularInline):
    model = ReviewScore
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('submission', 'reviewer', 'status',
                    'recommendation', 'completed_at')
    list_filter = ('status', 'recommendation')
    search_fields = ('submission__title', 'reviewer__username')
    inlines = (ReviewScoreInline,)


@admin.register(ReviewCriterion)
class ReviewCriterionAdmin(admin.ModelAdmin):
    list_display = ('name', 'conference', 'weight', 'min_score', 'max_score', 'order')
    list_filter = ('conference',)


@admin.register(ConflictOfInterest)
class ConflictOfInterestAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'submission', 'declared_at')
    search_fields = ('reviewer__username', 'submission__title')