import datetime
from django.contrib.auth.models import Group


def get_prev_month_year():
    date = datetime.date.today()
    prev_month = date.month - 1
    prev_year = date.year
    if prev_month == 0:
        prev_month = 12
        prev_year = prev_year - 1

    return (prev_month, prev_year)


def is_user_in_admin_group(user):
    try:
        admin_group = Group.objects.get(name='Admin')
        return admin_group in user.groups.all()
    except Group.DoesNotExist:
        return False


