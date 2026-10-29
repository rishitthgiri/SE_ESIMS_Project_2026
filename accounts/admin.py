from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SecurityEvent, User


@admin.register(User)
class ESIMSUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('ESIMS', {'fields': ('role',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('ESIMS', {'fields': ('email', 'role')}),)
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Read-only: security events are an audit record."""
    list_display = ('timestamp', 'event_type', 'username_attempted', 'user', 'ip_address', 'path')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('username_attempted', 'path', 'ip_address')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

