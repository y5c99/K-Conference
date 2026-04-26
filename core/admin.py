from django.contrib import admin
from .models import Announcement, FAQ, AuditLog


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'conference', 'audience', 'is_pinned', 'created_at')
    list_filter = ('conference', 'audience', 'is_pinned')
    search_fields = ('title', 'body')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'conference', 'is_published', 'order')
    list_filter = ('conference', 'is_published')
    search_fields = ('question', 'answer')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'target', 'conference', 'created_at')
    list_filter = ('action', 'conference')
    search_fields = ('target', 'notes', 'actor__username')
    readonly_fields = ('action', 'actor', 'target', 'conference',
                       'notes', 'created_at')