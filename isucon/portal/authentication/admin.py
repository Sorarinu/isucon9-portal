from django.contrib import admin

from isucon.portal.authentication.models import User, Team

class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "username", "is_staff"]
    list_filter = ["is_staff"]

admin.site.register(User, UserAdmin)


class TeamAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "is_active"]
    list_filter = ["is_active"]

admin.site.register(Team, TeamAdmin)
