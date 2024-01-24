from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.shortcuts import redirect


class ClientAdminConfig(admin.ModelAdmin):
    category = "Events & Clients"
    model = Client
    list_display = ['full_name', 'phone_number', 'total_revenue',
                    'total_pending_payment', 'active_events', 'past_events', 'bill', 'bill_link']
    search_fields = ("full_name__startswith",
                     "full_name__endswith", "phone_number")

    def changelist_view(self, request, extra_context=None):
        setattr(self, 'user', request.user)
        setattr(self, 'request', request)
        return super().changelist_view(request, extra_context)

    def total_revenue(self, obj):
        return obj.get_total_revenue()

    def total_pending_payment(self, obj):
        return obj.get_pending_payment()

    def active_events(self, obj):
        events = obj.get_active_events()
        table = ""
        for event in events:
            url = reverse("admin:billing_event_changelist", current_app=admin.site.name) + \
                "?" + urlencode({"id": f"{event.id}"})
            link = f"<a href={url}>{event}</a>"
            table = table + f"<tr><td>{link}</td></tr>"

        if table == "":
            return "No active events"
        return format_html(f"<table class='table table-responsive table-sm table-hover'>{table}</table>")

    def past_events(self, obj):
        events = obj.get_inactive_events()
        table = ""

        for event in events:
            url = reverse("admin:billing_event_changelist", current_app=admin.site.name) + \
                "?" + urlencode({"date": "Past events"}) + "&" + \
                urlencode({"id": f"{event.id}"})
            link = f"<a href={url}>{event}</a>"
            table = table + f"<tr><td>{link}</td></tr>"

        if table == "":
            return "No past events registered"

        return format_html(f"<table>{table}</table>")

    def bill(self, obj):
        if Bill.objects.filter(client=obj).exists():
            bill = Bill.objects.filter(client=obj).latest('date')
            url = reverse("billing:view-bill",
                          args=[bill.id], current_app=admin.site.name)
            return format_html('<a class="btn btn-success btn-sm" href={} onClick="CopyUrl(this)">Download bill</a>', url)
        else:
            client_id = obj.id
            url = reverse("billing:generate_new_bill",
                          args=[client_id], current_app=admin.site.name)
            return format_html(f"<a class='btn btn-warning text-light btn-sm' href={url} onClick='CopyUrl(this)'>Generate New bill</a>")

    def bill_link(self, obj):
        if Bill.objects.filter(client=obj).exists():
            bill = Bill.objects.filter(client=obj).latest('date')
            bill_link = {"link": reverse("billing:view-bill",
                                         args=[bill.id], current_app=admin.site.name)}
            return format_html('<div class="ttip"><a class="btn btn-info text-light btn-sm" href=# onClick="CopyUrlOnly({}, {})"><span class="ttiptext" id="{}">Copy to clipboard</span>Copy bill Link</a></div>', bill_link, obj.id, obj.id)
        else:
            return format_html('<a class="btn btn-secondary btn-sm disabled" href=#>Copy bill Link</a>')

    # Alters Form Behavior
    # After Client Form is saved takes to event Form

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse("admin:billing_event_add", current_app=admin.site.name))

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


admin.site.register(Client, ClientAdminConfig)

admin.site.register(Event)
