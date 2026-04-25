from django.contrib import admin
from .models import Conference, Track, Session, Registration


class TrackInline(admin.TabularInline):
    model = Track
    extra = 1


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = ('title', 'kind', 'starts_at', 'ends_at', 'track')


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organiser', 'start_date', 'end_date',
                    'mode', 'status')
    list_filter  = ('status', 'mode')
    search_fields = ('name', 'short_name', 'location')
    inlines = (TrackInline, SessionInline)
    date_hierarchy = 'start_date'


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'conference')
    list_filter  = ('conference',)
    search_fields = ('name',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'conference', 'kind', 'starts_at', 'ends_at')
    list_filter  = ('conference', 'kind')
    search_fields = ('title', 'speaker')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'conference', 'status', 'registered_at')
    list_filter  = ('status', 'conference')
    search_fields = ('user__username', 'user__email')