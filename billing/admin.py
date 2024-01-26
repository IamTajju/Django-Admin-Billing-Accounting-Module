from django.contrib import admin
from django.http.request import HttpRequest
from .models import *
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib.admin.utils import quote
from urllib.parse import quote as urlquote
from django.shortcuts import redirect
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib import messages
from django.http import HttpResponseRedirect
from .helpers import *
from .forms import *
from .filters import *
from datetime import timedelta
from .business_logic.services import create_inflow2bill, edit_inflow2bill


class ClientAdminConfig(admin.ModelAdmin):
    category = "Events & Clients"
    model = Client
    ordering = ('-date_added',)
    list_per_page = 25
    list_display = ['full_name', 'phone_number', 'total_revenue',
                    'total_pending_payment', 'active_events', 'past_events', 'bill', 'bill_link']
    search_fields = ("full_name__startswith",
                     "full_name__endswith", "phone_number")

    def total_revenue(self, obj):
        return obj.get_total_revenue()

    def total_pending_payment(self, obj):
        return obj.get_pending_payment()

    def active_events(self, obj):
        events = obj.get_active_events()
        return render_table(events, admin.site.name, "No Active events.", obj.id, "a", "See Events")

    def past_events(self, obj):
        events = obj.get_inactive_events()
        return render_table(events, admin.site.name, "No Past Events.", obj.id, "p", "See Events")

    def bill(self, obj):
        if Bill.objects.filter(client=obj).exists():
            bill = Bill.objects.filter(client=obj).latest('date')
            return render_button(bill, 'Download Bill', admin.site.name, 'btn-outline-success')
        else:
            client_id = obj.id
            url = reverse("billing:generate_new_bill",
                          args=[client_id], current_app=admin.site.name)
            return render_button(obj, 'Generate New Bill', admin.site.name, 'btn-warning', url)

    def bill_link(self, obj):
        if Bill.objects.filter(client=obj).exists():
            bill = Bill.objects.filter(client=obj).latest('date')
            return render_copy_link_button(bill, "Copy Bill Link", admin.site.name)
        else:
            return render_copy_link_button(obj.id, "Copy Bill Link", admin.site.name, True)

    # Alters Form Behavior
    # After Client Form is saved takes to event Form

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse("admin:billing_event_add", current_app=admin.site.name))

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_list_display(self, request):
        list_display = super().get_list_display(request)

        # Use a set to keep track of the columns
        existing_columns = set(list_display)

        # Columns to add conditionally
        conditional_columns = ['total_revenue', 'total_pending_payment']

        # Check if each column is already in the list_display and if the condition is met
        for column in conditional_columns:
            if column in existing_columns and user_belongs_to_group(request.user, 'Team Members'):
                list_display.remove(column)

        return list_display


class PackageAdminConfig(admin.ModelAdmin):
    model = Package
    list_display = ['action', 'name', 'active', 'get_qty_sold', 'coverage',
                    'budget', 'num_photographer', 'num_cinematographer']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # obj is not None, so this is an edit
            return ['budget']
        else:  # obj is None, so this is an add
            return []

    def action(self, obj):
        return render_admin_action_button(obj, "Edit", "change", admin.site.name, "btn-outline-primary")


class AddOnAdminConfig(admin.ModelAdmin):
    model = AddOn
    list_display = ['name', 'price', 'get_qty_sold']


class EventAdminConfig(admin.ModelAdmin):
    form = EventForm
    category = "Events & Clients"
    model = Event
    ordering = ('-date',)
    list_per_page = 15
    list_display = ['action', 'client_name', 'event_status_badge', 'payment_status_badge', 'event_type', 'selected_package', 'discount', 'discounted_budget', 'payment_received',
                    'date', 'venue', 'lead_by', 'covered_by', 'claim_conflicts', 'cost']

    list_filter = [EventFilter, 'package', 'event_status', 'payment_status']
    search_fields = ("client__full_name", "client__phone_number", 'package__name', 'event_type',
                     'add_ons__name', 'venue', 'event_status', 'payment_status')

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return False
        if not obj.is_active_event:
            return False
        return True

    def event_status_badge(self, obj):
        # Define the mapping of event status to badge class
        status_mapping = {
            'PR': 'badge bg-warning',
            'C': 'badge bg-info',
            'D': 'badge bg-success',
            'S': 'badge bg-danger',
        }

        # Get the badge class based on the event status
        badge_class = status_mapping.get(
            obj.event_status, 'badge bg-secondary')

        # Return the formatted HTML with the badge class
        return format_html('<span class="{}">{}</span>', badge_class, obj.get_event_status_display())

    event_status_badge.short_description = 'Event Status'

    def payment_status_badge(self, obj):
        # Define the mapping of payment status to badge class
        status_mapping = {
            'N': 'badge bg-danger',
            'P': 'badge bg-warning',
            'F': 'badge bg-success',
        }

        # Get the badge class based on the payment status
        badge_class = status_mapping.get(
            obj.payment_status, 'badge bg-secondary')

        # Return the formatted HTML with the badge class
        return format_html('<span class="{}">{}</span>', badge_class, obj.get_payment_status_display())

    payment_status_badge.short_description = 'Payment Status'

    def action(self, obj):
        if obj.is_active_event:
            button_text = 'Edit'
            button_class = 'btn-outline-info'
        else:
            button_text = 'Inactive'
            button_class = 'btn-dark disabled'
        return render_admin_action_button(obj, button_text, "change", admin.site.name, button_class)

    def lead_by(self, obj):
        leads = obj.lead_photographers.all()
        return render_table(leads, admin.site.name, "No Lead Assigned.", obj.id, "l", "See Leads")

    def covered_by(self, obj):
        photographers = obj.photographer.all()
        return render_table(photographers, admin.site.name, "No-one Assigned Yet.", obj.id, "p", "See TeamMembers")

    def client_name(self, obj):
        client = obj.client
        url = reverse("admin:billing_client_changelist",
                      current_app=admin.site.name) + "?" + urlencode({"id": f"{client.id}"}, )
        link = f"<a href={url}>{client}</a>"

        return format_html(f"{link}")

    def discounted_budget(self, obj):
        return obj.get_total_budget()

    def claim_conflicts(self, obj):
        return obj.get_claim_conflicts()

    def cost(self, obj):
        return obj.get_cost()

    def selected_package(self, obj):
        if obj.package is None:
            data = f"<p>One-Time Custom Package</p><br>"
        else:
            data = f"<p>{obj.package}</p><br>"

        add_ons = obj.add_ons.all()
        return format_html(data + render_table(add_ons, admin.site.name, "No add-ons selected.", obj.id, "a", "See Add-Ons"))

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        if "_save" in request.POST.keys():
            return redirect(reverse("billing:generate_new_bill_from_admin",
                                    args=[obj.client.id, "redirect"], current_app=admin.site.name))

        elif "_addanother" in request.POST:
            """
            Determine the HttpResponse for the add_view stage.
            """
            opts = obj._meta
            preserved_filters = self.get_preserved_filters(request)
            obj_url = reverse(
                "admin:%s_%s_change" % (opts.app_label, opts.model_name),
                args=(quote(obj.pk),),
                current_app=self.admin_site.name,
            )
            # Add a link to the object's change form if the user can edit the obj.
            if self.has_change_permission(request, obj):
                obj_repr = format_html(
                    '<a href="{}">{}</a>', urlquote(obj_url), obj)
            else:
                obj_repr = str(obj)
            msg_dict = {
                "name": opts.verbose_name,
                "obj": obj_repr,
            }
            msg = format_html(
                _(
                    "The {name} “{obj}” was added successfully. You may add another "
                    "{name} below."
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

    def response_change(self, request, obj, post_url_continue=None):
        if "_save" in request.POST.keys():
            return redirect(reverse("billing:generate_new_bill_from_admin",
                                    args=[obj.client.id, "redirect"], current_app=admin.site.name))

        elif "_addanother" in request.POST:
            """
            Determine the HttpResponse for the add_view stage.
            """
            opts = obj._meta
            preserved_filters = self.get_preserved_filters(request)
            obj_url = reverse(
                "admin:%s_%s_change" % (opts.app_label, opts.model_name),
                args=(quote(obj.pk),),
                current_app=self.admin_site.name,
            )
            # Add a link to the object's change form if the user can edit the obj.
            if self.has_change_permission(request, obj):
                obj_repr = format_html(
                    '<a href="{}">{}</a>', urlquote(obj_url), obj)
            else:
                obj_repr = str(obj)
            msg_dict = {
                "name": opts.verbose_name,
                "obj": obj_repr,
            }
            msg = format_html(
                _(
                    "The {name} “{obj}” was added successfully. You may add another "
                    "{name} below."
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

    def get_list_display(self, request):
        list_display = super().get_list_display(request)

        # Use a set to keep track of the columns
        existing_columns = set(list_display)

        # Columns to add conditionally
        conditional_columns = ['discount', 'discounted_budget',
                               'payment_received', 'payment_status_badge']

        # Check if each column is already in the list_display and if the condition is met
        for column in conditional_columns:
            if column in existing_columns and user_belongs_to_group(request.user, 'Team Members'):
                list_display.remove(column)

        return list_display


class InflowAdminConfig(admin.ModelAdmin):
    form = InflowForm
    model = CashInflow
    search_fields = ['source__full_name']
    list_display = ['action', 'source_of_payment',
                    'amount', 'bill']

    list_filter = (InflowFilter, 'source',)

    def bill(self, obj):
        return render_button(InflowToBill.objects.get(inflow=obj).bill, 'Download Bill', admin.site.name, 'btn-outline-success')

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return False
        if not obj.is_active:
            return False
        return True

    def action(self, obj):
        if obj.is_active:
            button_text = 'Edit'
            button_class = 'btn-outline-info'
        else:
            button_text = 'Inactive'
            button_class = 'btn-dark disabled'
        return render_admin_action_button(obj, button_text, "change", admin.site.name, button_class)

    def get_form(self, request, obj, **kwargs):
        if obj == None:
            return super().get_form(request, obj, **kwargs)
        cash_inflow_instance = CashInflow.objects.get(id=obj.id)
        if cash_inflow_instance.source is not None:
            client = cash_inflow_instance.source
            pending_payment = client.get_pending_payment()
            help_texts = {
                "amount": f"Total pending payment for {client.full_name} is BDT {pending_payment}"}
            kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)

    def source_of_payment(self, obj):
        source = obj.source
        if source is not None:
            url = reverse("admin:billing_client_changelist", current_app=admin.site.name) + \
                "?" + urlencode({"id": f"{source.id}"})

            link = f"<a href={url}>{source}</a>"
            return format_html(link)
        else:
            return format_html("Non Income Inflow")

    def get_fields(self, request, obj=None):
        if obj is None:
            return ('source',)
        else:
            return ('amount',)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = []
        if obj is not None:
            readonly_fields.append('source')
        return readonly_fields

    def response_add(self, request, obj, post_url_continue=None):
        url = f'/admin/billing/cashinflow/{obj.id}/change'
        return redirect(url)

    def response_change(self, request, obj):
        if obj.source is not None:
            if InflowToBill.objects.filter(inflow=obj).exists():
                bill_id = edit_inflow2bill(obj, request, "return bill id")
            else:
                bill_id = create_inflow2bill(obj, request, "return bill id")
            return redirect(reverse("billing:view_bill_from_admin",
                                    args=[bill_id, "redirect"], current_app=admin.site.name))

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


class LedgerAdminConfig(admin.ModelAdmin):
    model = Ledger
    list_display = ['for_month', 'for_year', 'cash_balance', 'advance_received',
                    'revenue', 'cogs', 'gross_profit', 'expenses', 'net_profit']

    list_filter = ('year',)

    ordering = ('-year', '-month')

    def for_year(self, obj):
        return str(obj.year)

    def for_month(self, obj):
        return datetime.datetime.strptime(str(obj.month), "%m").strftime("%B")


class TeamMemberBillAdminConfig(admin.ModelAdmin):
    model = TeamMemberBill
    list_display = ['action', 'team_member', 'for_month', 'covered_events',
                    'bill_for_events', 'adjustment', 'comment', 'total_receivable', 'cleared']

    list_filter = ['year']

    def save_model(self, request, obj, form, change):
        user = User.objects.get(id=request.user.id)
        obj.team_member = TeamMember.objects.get(user=user)
        obj.save()

    def action(self, obj):
        if obj.cleared:
            button_text = 'Inactive'
            button_class = 'btn-dark disabled'
        else:
            button_text = 'Edit'
            button_class = 'btn-outline-info'
        return render_admin_action_button(obj, button_text, "change", admin.site.name, button_class)

    def covered_events(self, obj):
        events = obj.events.all()
        return render_table(events, admin.site.name, "No events covered.", obj.id, "a", "See Events Covered")

    def bill_for_events(self, obj):
        return obj.get_total_bill() - obj.adjustment

    def for_month(self, obj):
        return datetime.datetime.strptime(str(obj.month), "%m").strftime("%B")

    def total_receivable(self, obj):
        return obj.get_total_bill()

    def get_queryset(self, request):
        qs = super(TeamMemberBillAdminConfig, self).get_queryset(request)
        user = User.objects.get(id=request.user.id)
        if user.is_superuser or is_user_in_admin_group(user):
            return qs

        team_member = TeamMember.objects.get(user=user)
        return qs.filter(team_member=team_member)

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


class OutflowAdminConfig(admin.ModelAdmin):
    model = CashOutflow
    list_display = ['action', 'type', 'source_of_expense',
                    'amount', 'for_month', 'date_cleared']

    list_filter = ('source', OutflowFilter)

    def get_form(self, request, obj, **kwargs):
        if obj is not None:
            if User.objects.filter(username=obj.source).exists():
                team_member_bill = OutflowToTeamMemberBill.objects.get(
                    cash_outflow=obj).team_member_bill
                tmb_adminConfig_instance = TeamMemberBillAdminConfig
                amount = TeamMemberBillAdminConfig.bill_for_events(
                    tmb_adminConfig_instance, team_member_bill)
                adjustment = team_member_bill.adjustment
                comment = team_member_bill.comment
                help_texts = {
                    "amount": f"Bill for events: BDT {amount} | Adjustments: BDT {adjustment} for {comment} | Total: {adjustment+amount}"}
                kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)

    def action(self, obj):
        type = self.type(obj)
        if type == "Overhead":
            button_text = "Edit"
            button_class = "btn-outline-primary"
        else:
            button_text = "Clear Payment"
            button_class = "btn-warning"

        if not obj.is_active:
            button_class = "btn-warning disabled"

        return render_admin_action_button(obj, button_text, "change", admin.site.name, button_class)

    def type(self, obj):
        if User.objects.filter(username=obj.source).exists():
            return "Payroll"
        else:
            return "Overhead"

    def source_of_expense(self, obj):
        if User.objects.filter(username=obj.source).exists():
            team_member = TeamMember.objects.get(
                user=User.objects.get(username=obj.source))

            team_member_bill = TeamMemberBill.objects.get(
                team_member=team_member, month=obj.month, year=obj.year)

            url = reverse("admin:billing_teammemberbill_changelist", current_app=admin.site.name) + \
                "?" + urlencode({"id": f"{team_member_bill.id}"})
            link = f"<a href={url}>{str(team_member_bill)}</a>"
            return format_html(link)

        return obj.source

    def for_month(self, obj):
        return datetime.datetime.strptime(str(obj.month), "%m").strftime("%B")

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


class BillAdminConfig(admin.ModelAdmin):
    model = Bill
    list_display = ['client', 'user', 'date', 'download_bill']
    list_filter = ['client', 'user']

    def has_add_permission(self, request: HttpRequest):
        return False

    def download_bill(self, obj):
        return render_button(obj, 'Download Bill', admin.site.name, 'btn-outline-success')


admin.site.register(Client, ClientAdminConfig)
admin.site.register(Package, PackageAdminConfig)
admin.site.register(AddOn, AddOnAdminConfig)
admin.site.register(Event, EventAdminConfig)
admin.site.register(CashInflow, InflowAdminConfig)
admin.site.register(Ledger, LedgerAdminConfig)
admin.site.register(TeamMemberBill, TeamMemberBillAdminConfig)
admin.site.register(CashOutflow, OutflowAdminConfig)
admin.site.register(Bill, BillAdminConfig)
