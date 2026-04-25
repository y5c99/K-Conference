"""
Admin configuration for the 'accounts' app.
We show the Profile inline on the User edit page so organisers
can quickly change roles in the Django admin.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    """Show Profile fields inside the User admin page."""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """Custom User admin that includes the Profile inline."""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'get_role', 'is_staff')

    def get_role(self, instance):
        try:
            return instance.profile.get_role_display()
        except Profile.DoesNotExist:
            return '-'
    get_role.short_description = 'Role'


# Re-register User with our enhanced admin.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Also register Profile on its own (handy for searches).
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'affiliation', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'affiliation')