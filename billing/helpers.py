import datetime
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode


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


def render_table(objects, current_app, null_message, id, identifier, button_text):
    table = ""

    for object in objects:
        url = reverse(f"admin:{objects.model._meta.app_label}_{objects.model._meta.model_name}_changelist", current_app=current_app) + \
            "?" + urlencode({"id": f"{object.id}"})
        link = f"<a href={url}>{object}</a>"
        table = table + f"<tr><td>{link}</td></tr>"

    if table == "":
        return format_html(f"<small>{null_message}</small>")

    return format_html(
        f'<p class="d-inline-flex gap-1"><a class="btn btn-outline-primary btn-sm p-1" data-bs-toggle="collapse" href="#{identifier}{id}" role="button" aria-expanded="false" aria-controls="{identifier}{id}"><small>{button_text}</small></a></p><div class="collapse collapse-horizontal" id="{identifier}{id}"><div class="card card-body"><table class="table table-responsive table-sm table-hover">{table}</table></div></div>'
    )
    # return format_html(f"<table class='table table-responsive table-sm table-hover'>{table}</table>")


def render_button(object, button_text, current_app, button_class, url=None):
    if not url:
        url = reverse(f"{object._meta.app_label}:view-{object._meta.model_name}",
                      args=[object.id], current_app=current_app)
    return format_html(f'<a class="btn {button_class} btn-sm p-1" href={url} onClick="CopyUrl(this)"><small>{button_text}</small></a>')


def render_copy_link_button(object, button_text, current_app, disabled=False):
    if not disabled:
        bill_link = {"link": reverse(f"{object._meta.app_label}:view-{object._meta.model_name}",
                                     args=[object.id], current_app=current_app)}

        return format_html('<div class="ttip"><a class="btn btn-outline-info text-light btn-sm p-1" href=# onClick="CopyUrlOnly({}, {})"><span class="ttiptext" id="{}">Copy to clipboard</span><small>{}</small></a></div>', bill_link, object.id, object.id, button_text)
    return format_html(f'<a class="btn btn-outline-info text-light btn-sm p-1 disabled" href=#"><small>{button_text}</small></a>')


def render_admin_action_button(object, button_text, action, current_app, button_class, url=None):
    if not url:
        url = reverse(f"admin:{object._meta.app_label}_{object._meta.model_name}_{action}",
                      args=[object.id], current_app=current_app)
    return format_html(f'<a class="btn {button_class} btn-sm p-1" href={url}><small>{button_text}</small></a>')



def user_belongs_to_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
        return group in user.groups.all()
    except Group.DoesNotExist:
        return False
