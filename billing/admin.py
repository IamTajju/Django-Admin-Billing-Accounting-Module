from django.contrib import admin
from .models import *
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from user.models import *
from django.utils.http import urlencode
from django.urls import NoReverseMatch
from django.utils.text import capfirst
from django.contrib.admin import AdminSite
from django.apps import apps
from billing.forms import *
from billing.filters import *
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import quote
from urllib.parse import quote as urlquote
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext as _
from datetime import timedelta
# Register your models here.


class ClientAdminConfig(admin.ModelAdmin):
    category = "Events & Clients"
    model = Client
    list_display = ['full_name', 'phone_number', 'total_revenue',
                    'total_pending_payment', 'active_events', 'past_events', 'bill', 'bill_link']
    search_fields = ("full_name__startswith",)

    list_filter = [ClientFilter, ]

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
            url = reverse("admin:billing_event_changelist", current_app=admin_site.name) + \
                "?" + urlencode({"id": f"{event.id}"})
            link = f"<a href={url}>{event}</a>"
            table = table + f"<tr><td>{link}</td></tr>"

        if table == "":
            return "No active events"
        return format_html(f"<table>{table}</table>")

    def past_events(self, obj):
        events = obj.get_inactive_events()
        table = ""

        for event in events:
            url = reverse("admin:billing_event_changelist", current_app=admin_site.name) + \
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
                          args=[bill.id], current_app=admin_site.name)
            return format_html('<a class="btn btn-success btn-sm" href={} onClick="CopyUrl(this)">Download bill</a>', url)
        else:
            client_id = obj.id
            url = reverse("billing:generate_new_bill",
                          args=[client_id], current_app=admin_site.name)
            return format_html(f"<a class='btn btn-warning text-light btn-sm' href={url} onClick='CopyUrl(this)'>Generate New bill</a>")

    def bill_link(self, obj):
        if Bill.objects.filter(client=obj).exists():
            bill = Bill.objects.filter(client=obj).latest('date')
            bill_link = {"link": reverse("billing:view-bill",
                                         args=[bill.id], current_app=admin_site.name)}
            return format_html('<div class="ttip"><a class="btn btn-info text-light btn-sm" href=# onClick="CopyUrlOnly({}, {})"><span class="ttiptext" id="{}">Copy to clipboard</span>Copy bill Link</a></div>', bill_link, obj.id, obj.id)
        else:
            return format_html('<a class="btn btn-secondary btn-sm disabled" href=#>Copy bill Link</a>')

    # Alters Form Behavior
    # After Client Form is saved takes to event Form

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse("admin:billing_event_add", current_app=admin_site.name))

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


class PackageAdminConfig(admin.ModelAdmin):
    category = 'Service Detail'
    model = Package
    list_display = ['name', 'active', 'get_qty_sold', 'coverage',
                    'budget', 'num_photographer', 'num_cinematographer']

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


class AddOnAdminConfig(admin.ModelAdmin):
    category = 'Service Detail'
    model = AddOn
    list_display = ['name', 'price', 'get_qty_sold']

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


class EventAdminConfig(admin.ModelAdmin):
    form = EventForm
    category = "Events & Clients"
    model = Event
    list_display = ['action', 'client_name', 'event_status', 'payment_status', 'is_active_event', 'event_type', 'selected_package', 'discount', 'discounted_budget', 'payment_received',
                    'date', 'venue', 'lead_by', 'covered_by', 'claim_conflicts', 'cost']

    list_filter = (EventFilter, 'event_status', 'payment_status', 'client')

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return False
        if not obj.is_active_event:
            return False
        return True

    def action(self, obj):
        if not obj.is_active_event:
            return format_html("<button class='btn btn-dark btn-sm' type='submit' disabled>Cannot be changed</button>")
        url = reverse("admin:billing_event_change", args=(
            obj.id,), current_app=admin_site.name)
        link = f"<a class='btn btn-info btn-sm' href={url}>Edit</a>"
        return format_html(f"{link}")

    def lead_by(self, obj):
        table = ""
        for photographer in obj.lead_photographers.all():
            table = table + f"<tr><td>{photographer}</td></tr>"

        if table == "":
            return "No leads assigned."

        return format_html(f"<table>{table}</table>")

    def covered_by(self, obj):
        table = ""
        for team_member_bill in obj.photographer.all():
            url = reverse("admin:billing_teammemberbill_changelist",
                          current_app=admin_site.name) + "?" + urlencode({"id": f"{team_member_bill.id}"})
            link = f"<a href={url}>{team_member_bill.team_member}</a>"
            table = table + f"<tr><td>{link}</td></tr>"

        if table == "":
            return "No photographers/cinematographers assigned yet."

        return format_html(f"<table>{table}</table>")

    def client_name(self, obj):
        client = obj.client
        url = reverse("admin:billing_client_changelist",
                      current_app=admin_site.name) + "?" + urlencode({"id": f"{client.id}"}, )
        link = f"<a href={url}>{client}</a>"

        return format_html(f"{link}")

    def discounted_budget(self, obj):
        return obj.get_total_budget()

    def claim_conflicts(self, obj):
        conflict = ""
        num_photographers = 0
        num_cinematographers = 0
        for team_member_bill in obj.photographer.all():
            if team_member_bill.team_member.role == 'P':
                num_photographers = num_photographers + 1
            if team_member_bill.team_member.role == 'C':
                num_cinematographers = num_cinematographers + 1
        if obj.package:
            if obj.package.num_photographer < num_photographers:
                conflict = conflict + \
                    f"{num_photographers - obj.package.num_photographer} extra photographer(s)"

            if obj.package.num_cinematographer < num_cinematographers:
                conflict = conflict + " & " + \
                    f"{num_cinematographers - obj.package.num_cinematographer} extra cinematographer(s)"
        if conflict == "":
            conflict = "No conflicts found."

        return f"{conflict}"

    def cost(self, obj):
        cost = 0
        for team_member_bill in obj.photographer.all():
            if User.objects.filter(username=team_member_bill.team_member).exists():
                team_member = TeamMember.objects.get(
                    user=User.objects.get(username=team_member_bill.team_member))
                cost = cost + team_member.payment_per_event
        return cost

    def selected_package(self, obj):
        if obj.package is None:
            table = f"<p>No Package selected</p>"
        else:
            table = f"<p>{obj.package}</p>"

        if len(obj.add_ons.all()) == 0:
            table = table + "<tr><td>No add-ons selected</td></tr>"
        else:
            for add_on in obj.add_ons.all():
                table = table + f"<tr><td>{add_on.name}</td></tr>"

        return format_html(f"<table>{table}</table>")

    selected_package.short_description = "Package/Add-Ons"

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        if "_save" in request.POST.keys():
            client_admin_config_instance = ClientAdminConfig
            client = obj.client
            user_id = request.user.id
            return redirect(reverse("billing:generate_new_bill",
                                    args=[obj.client.id], current_app=admin_site.name))

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
            client_admin_config_instance = ClientAdminConfig
            client = obj.client
            user_id = request.user.id
            return redirect(reverse("billing:generate_new_bill",
                                    args=[obj.client.id], current_app=admin_site.name))

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


class InflowAdminConfig(admin.ModelAdmin):
    form = InflowForm
    category = "Finance"
    model = CashInflow
    list_display = ['action', 'source_of_payment',
                    'amount']

    list_filter = ('source', InflowFilter)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return False
        if (obj.date.month != datetime.datetime.now().month) or (obj.date.year != datetime.datetime.now().year):
            return False
        return True

    def action(self, obj):
        if (obj.date.month != datetime.datetime.now().month) or (obj.date.year != datetime.datetime.now().year):
            return format_html("<button class='btn btn-dark btn-sm' type='submit' disabled>Cannot be changed</button>")

        url = reverse("admin:billing_cashinflow_change", args=(
            obj.id,), current_app=admin_site.name)
        link = f"<a class='btn btn-info btn-sm' href={url}>Edit</a>"
        return format_html(f"{link}")

    def get_form(self, request, obj, **kwargs):
        if obj == None:
            return super().get_form(request, obj, **kwargs)
        cash_inflow_instance = CashInflow.objects.get(id=obj.id)
        if cash_inflow_instance.source is not None:
            client = cash_inflow_instance.source
            client_adminConfig_instance = ClientAdminConfig
            pending_payment = ClientAdminConfig.total_pending_payment(
                client_adminConfig_instance, client)
            help_texts = {
                "amount": f"Total pending payment for {client.full_name} is BDT {pending_payment}"}
            kwargs.update({"help_texts": help_texts})
        return super().get_form(request, obj, **kwargs)

    def source_of_payment(self, obj):
        source = obj.source
        if source is not None:
            url = reverse("admin:billing_client_changelist", current_app=admin_site.name) + \
                "?" + urlencode({"id": f"{source.id}"})

            link = f"<a href={url}>{source}</a>"
            return format_html(link)
        else:
            return format_html("Reminiscence Inflow")

    def get_fields(self, request, obj=None):
        if obj is None:
            return ('source',)
        else:
            return ('amount', 'editing')

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
            client = obj.source
            return redirect(reverse("billing:generate_new_bill",
                                    args=[client.id], current_app=admin_site.name))

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def generate_bill(self, obj):
        if Bill.objects.filter(client=obj.source,  date__gte=(obj.date - timedelta(seconds=15)), date__lte=(obj.date + timedelta(seconds=15))).exists():
            bill = Bill.objects.filter(client=obj.source,  date__gte=(
                obj.date - timedelta(seconds=30)), date__lte=(obj.date + timedelta(seconds=15)))[0]
            url = reverse("billing:generate-bill-pdf",
                          args=[bill.id], current_app=admin_site.name)
            return format_html('<a class="btn btn-success btn-sm" href={} onClick="CopyUrl(this)">Download bill</a>', url)
        else:
            return format_html('<a class="btn btn-secondary btn-sm disabled" href=#>Download bill</a>')

    def bill_link(self, obj):
        if Bill.objects.filter(client=obj.source,  date__gte=(obj.date - timedelta(seconds=30)), date__lte=(obj.date + timedelta(seconds=30))).exists():
            bill = Bill.objects.filter(client=obj.source,  date__gte=(
                obj.date - timedelta(seconds=30)), date__lte=(obj.date + timedelta(seconds=30)))[0]
            bill_link = {"link": reverse("billing:generate-bill-pdf",
                                         args=[bill.id], current_app=admin_site.name)}
            return format_html('<div class="ttip"><a class="btn btn-info text-light btn-sm" href=# onClick="CopyUrlOnly({}, {})"><span class="ttiptext" id="{}">Copy to clipboard</span>Copy bill Link</a></div>', bill_link, obj.id, obj.id)
        else:
            return format_html('<a class="btn btn-secondary btn-sm disabled" href=#>Copy Bill Link</a>')


class OutflowAdminConfig(admin.ModelAdmin):
    category = "Finance"
    model = CashOutflow
    list_display = ['action', 'is_active', 'type', 'source_of_expense',
                    'amount', 'for_month', 'date_cleared']

    # list_filter = ('source', OutflowFilter)

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
        url = reverse("admin:billing_cashoutflow_change",
                      args=(obj.id,), current_app=admin_site.name)
        if type == "Overhead":
            return format_html('<a class="btn btn-info btn-sm" href={}>Edit expense</a>', url)
        else:
            return format_html('<a class="btn btn-info btn-sm" href={}>Clear payment</a>', url)
            if obj.amount == 0:
                return format_html('<a class="btn btn-info btn-sm" href={}>Clear payment</a>', url)
            else:
                return format_html('<button class="btn btn-sm btn-dark" disabled>Clear Payment</button>')

    def type(self, obj):
        if User.objects.filter(username=obj.source).exists():
            return "Payroll"
        else:
            return "Overhead"

    # def payroll_month(self, obj):
    #     if self.type(obj) == "Payroll":
    #         return datetime.datetime.strptime(str(obj.month), "%m").strftime("%B")
    #     return "-"

    def source_of_expense(self, obj):
        if User.objects.filter(username=obj.source).exists():
            team_member = TeamMember.objects.get(
                user=User.objects.get(username=obj.source))

            team_member_bill = TeamMemberBill.objects.get(
                team_member=team_member, month=obj.month, year=obj.year)

            url = reverse("admin:billing_teammemberbill_changelist", current_app=admin_site.name) + \
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


class LedgerAdminConfig(admin.ModelAdmin):
    category = "Income Statement"
    model = Ledger
    list_display = ['for_month', 'for_year', 'cash_balance', 'advance_received',
                    'revenue', 'cogs', 'gross_profit', 'expenses', 'net_profit']

    # list_filter = (MonthFilter, YearFilter)

    def cash_balance(self, obj):
        date = datetime.date.today()
        if obj.year < date.year:
            return obj.end_balance
        elif obj.month < date.month:
            return obj.end_balance
        else:
            return obj.cash

    def gross_profit(self, obj):
        return obj.revenue - obj.cogs

    def net_profit(self, obj):
        return obj.revenue - obj.cogs - obj.expenses

    def for_year(self, obj):
        return str(obj.year)

    def for_month(self, obj):
        return datetime.datetime.strptime(str(obj.month), "%m").strftime("%B")


class TeamMemberBillAdminConfig(admin.ModelAdmin):
    form = TeamMemberBillForm
    category = "Team"
    model = TeamMemberBill
    list_display = ['action', 'team_member', 'for_month', 'covered_events',
                    'bill_for_events', 'adjustment', 'comment', 'total_receivable', 'cleared']

    list_filter = ['month', 'year']

    def action(self, obj):
        url = reverse("admin:billing_teammemberbill_change",
                      args=(obj.id,), current_app=admin_site.name)
        if obj.cleared:
            return format_html('<button class="btn btn-info btn-sm" disabled>Edit record</button>')

        return format_html('<a class="btn btn-info btn-sm" href={}>Edit record</a>', url)

    def covered_events(self, obj):
        table = ""
        for event in obj.events.all():
            url = reverse("admin:billing_event_changelist",
                          current_app=admin_site.name) + "?" + urlencode({"id": f"{event.id}"})
            link = f"<a href={url}>{event}</a>"
            table = table + f"<tr><td>{link}</td></tr>"

        if table == "":
            return "No event covered"

        return format_html(f"<table>{table}</table>")

    def has_add_permission(self, request):
        user = User.objects.get(id=request.user.id)
        try:
            team_member = TeamMember.objects.get(user=user)
        except:
            return True
        prev_month = datetime.date.today().month - 1
        prev_year = datetime.date.today().year
        if prev_month == 0:
            prev_month = 12
            prev_year = prev_year - 1

        if TeamMemberBill.objects.filter(team_member=team_member, month=prev_month, year=prev_year).exists():
            return False
        return True

    def save_model(self, request, obj, form, change):
        user = User.objects.get(id=request.user.id)
        obj.team_member = TeamMember.objects.get(user=user)
        obj.save()

    def bill_for_events(self, obj):
        return obj.get_total_bill() - obj.adjustment

    def for_month(self, obj):
        return datetime.datetime.strptime(str(obj.month), "%m").strftime("%B")

    def total_receivable(self, obj):
        return obj.get_total_bill()

    def get_queryset(self, request):
        qs = super(TeamMemberBillAdminConfig, self).get_queryset(request)
        if request.user.is_superuser or request.user.username == "Adnan":
            return qs
        user = User.objects.get(id=request.user.id)
        team_member = TeamMember.objects.get(user=user)
        return qs.filter(team_member=team_member)

    def changeform_view(self, request, object_id, form_url, extra_context=None):
        extra_context = {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


class BillAdminConfig(admin.ModelAdmin):
    category = "Income Statement"
    model = Bill
    list_display = ['client', 'user', 'date', 'view_bill']

    def view_bill(self, obj):
        url = reverse("billing:view-bill",
                      args=[obj.id], current_app=admin_site.name)
        link = f"<a class='btn btn-sm btn-info px-1' href={url} class='past-bill-btn' onClick='CopyUrl(this)'>Download Bill</a>"
        return format_html(link)


class InflowToBillAdminConfig(admin.ModelAdmin):
    model = InflowToBill
    list_display = ['inflow', 'bill', 'date']


class InflowToEventAdminConfig(admin.ModelAdmin):
    model = InflowToEvent
    list_display = ['inflow', 'event', 'amount']


class ReminiscenceAdminSite(AdminSite):
    site_title = "Billing & Accounting Module"
    site_header = "Billing & Accounting Module"
    index_title = "Billing & Accounting Module"

    def _build_app_dict(self, request, label=None):
        app_dict = {}

        if label:
            models = {
                m: m_a for m, m_a in self._registry.items()
                if m._meta.app_label == label
            }
        else:
            models = self._registry

        for model, model_admin in models.items():
            actual_app_name = model._meta.app_label
            app_label = getattr(model_admin, 'category',
                                None) or model._meta.app_label

            has_module_perms = model_admin.has_module_permission(request)
            if not has_module_perms:
                continue

            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True not in perms.values():
                continue

            info = (actual_app_name, model._meta.model_name)
            model_dict = {
                'name': capfirst(model._meta.verbose_name_plural),
                'object_name': model._meta.object_name,
                'perms': perms,
            }
            if perms.get('change'):
                try:
                    model_dict['admin_url'] = reverse(
                        'admin:%s_%s_changelist' % info, current_app=self.name)
                except NoReverseMatch:
                    pass
            if perms.get('view'):
                try:
                    model_dict['admin_url'] = reverse(
                        'admin:%s_%s_changelist' % info, current_app=self.name)
                except NoReverseMatch:
                    pass
            else:
                model_dict['admin_url'] = None

            if perms.get('add'):
                try:
                    model_dict['add_url'] = reverse(
                        'admin:%s_%s_add' % info, current_app=self.name)
                except NoReverseMatch:
                    pass

            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                app_dict[app_label] = {
                    'name': app_label,
                    'app_label': app_label,
                    'app_url': '',
                    'has_module_perms': has_module_perms,
                    'models': [model_dict],
                }

        if label:
            return app_dict.get(label)
        return app_dict

    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request, app_label)

        # Sort the apps alphabetically.
        if app_dict is not None:
            app_list = sorted(app_dict.values(),
                              key=lambda x: x["name"].lower())

        # Sort the models alphabetically within each app.
            for app in app_list:
                app["models"].sort(key=lambda x: x["name"])

            return app_list
        return None

    def app_index(self, request, app_label, extra_context=None):
        app_list = self.get_app_list(request, app_label)

        if not app_list:
            return redirect("/admin")

        context = {
            **self.each_context(request),
            "title": _("%(app)s administration") % {"app": app_list[0]["name"]},
            "subtitle": None,
            "app_list": app_list,
            "app_label": app_label,
            **(extra_context or {}),
        }

        request.current_app = self.name

        return TemplateResponse(
            request,
            self.app_index_template
            or ["admin/%s/app_index.html" % app_label, "admin/app_index.html"],
            context,
        )


admin_site = ReminiscenceAdminSite(name='reminiscence-erp')
admin_site.register(Client, ClientAdminConfig)
admin_site.register(Package, PackageAdminConfig)
admin_site.register(AddOn, AddOnAdminConfig)
admin_site.register(Event, EventAdminConfig)
admin_site.register(TeamMemberBill, TeamMemberBillAdminConfig)
admin_site.register(CashInflow, InflowAdminConfig)
admin_site.register(CashOutflow, OutflowAdminConfig)
admin_site.register(Ledger, LedgerAdminConfig)
admin_site.register(Bill, BillAdminConfig)
