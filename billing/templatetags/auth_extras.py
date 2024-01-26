from django import template
from django.contrib.auth.models import Group

import logging
register = template.Library()


@register.filter(name="has_admin_privilege")
def has_admin_privilege(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()
