from django.contrib import admin
from .models import Submission, SubmissionFile


class SubmissionFileInline(admin.TabularInline):
    model = SubmissionFile
    extra = 0
    readonly_fields = ('uploaded_at', 'uploaded_by', 'version')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('submission_id_code', 'title', 'author',
                    'conference', 'track', 'status', 'submitted_at')
    list_filter = ('status', 'conference', 'track')
    search_fields = ('title', 'submission_id_code',
                     'author__username', 'author__email')
    readonly_fields = ('submission_id_code', 'created_at', 'updated_at')
    inlines = (SubmissionFileInline,)


@admin.register(SubmissionFile)
class SubmissionFileAdmin(admin.ModelAdmin):
    list_display = ('submission', 'version', 'uploaded_at', 'uploaded_by')
    list_filter = ('uploaded_at',)