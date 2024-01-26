from django.contrib import admin
from .models import *
# Register your models here.


class TeamMemberAdminConfig(admin.ModelAdmin):
    category = "Team"
    model = TeamMember
    list_display = ['name', 'role', 'payment_per_event']

    def name(self, obj):
        name = obj.user.username
        return name


admin.site.register(TeamMember, TeamMemberAdminConfig)
