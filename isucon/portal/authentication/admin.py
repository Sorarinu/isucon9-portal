from django.utils.translation import gettext, gettext_lazy as _
from django.contrib import admin

from isucon.portal.authentication.models import User, Team

class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "username", "display_name", "team", "is_student", "is_staff"]
    list_filter = ["is_staff"]

    fieldsets = (
        (None, {'fields': ('username', 'display_name', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(User, UserAdmin)


class TeamAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "is_active", "benchmarker"]
    list_filter = ["is_active"]

admin.site.register(Team, TeamAdmin)
