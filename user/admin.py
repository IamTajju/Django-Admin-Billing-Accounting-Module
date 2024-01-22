from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from billing.admin import admin_site, ReminiscenceAdminSite
# Register your models here.


class TeamMemberAdminConfig(admin.ModelAdmin):
    category = "Team"
    model = TeamMember
    list_display = ['name', 'role', 'payment_per_event']

    def name(self, obj):
        name = obj.user.username
        return format_html(f'{name}')


# admin_site.register(TeamMember, TeamMemberAdminConfig)
# admin_site.register(User, UserAdmin)
# admin_site.register(Group)
