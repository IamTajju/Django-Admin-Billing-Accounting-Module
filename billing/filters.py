from django.contrib import admin
from billing.models import *
import calendar
import logging
from django.utils.translation import gettext_lazy as _


class EventFilter(admin.SimpleListFilter):
    title = 'Active Events'
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return (
            (('Past events'), _('Past events')),
            (('Active events'), _('Active events'))
        )

    def queryset(self, request, queryset):
        # Code logic should mimick Client method -> get_active_events
        if not self.value() or (self.value() == 'Active events'):
            current_date = datetime.date.today()
            q1 = queryset.exclude(event_status='D', payment_status='F')
            q2 = queryset.filter(
                date__month=current_date.month, date__year=current_date.year)
            return q1 | q2
        if self.value() == 'Past events':
            current_date = datetime.date.today()
            return queryset.exclude(
                date__month=current_date.month, date__year=current_date.year).filter(event_status='D', payment_status='F')


class InflowFilter(admin.SimpleListFilter):
    title = 'Active Inflows'
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return (
            (('Past Inflows'), _('Past Inflows')),
            (('Active Inflows'), _('Active Inflows'))
        )

    def queryset(self, request, queryset):
        # Code logic should mimick Client method -> get_active_events
        if not self.value() or (self.value() == 'Active Inflows'):
            current_date = datetime.datetime.now()
            return queryset.filter(
                date__month=current_date.month, date__year=current_date.year)

        if self.value() == 'Past Inflows':
            current_date = datetime.datetime.now()
            return queryset.exclude(
                date__month=current_date.month, date__year=current_date.year)


class ClientFilter(admin.SimpleListFilter):
    title = 'Active Clients'
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return (
            (('Inactive Clients'), _('Inactive Clients')),
            (('Active Clients'), _('Active Clients'))
        )

    def queryset(self, request, queryset):
        clients = Client.objects.all()
        if not self.value() or (self.value() == 'Active Clients'):
            for client in clients:
                if len(client.get_active_events()) == 0:
                    queryset = queryset.exclude(id=client.id)
            return queryset

        if self.value() == 'Inactive Clients':
            for client in clients:
                if len(client.get_active_events()) != 0:
                    queryset = queryset.exclude(id=client.id)
            return queryset


class OutflowFilter(admin.SimpleListFilter):
    title = 'Active Inflows'
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return (
            (('Past Outflows'), _('Past Outflows')),
            (('Active Outflows'), _('Active Outflows'))
        )

    def queryset(self, request, queryset):
        # Code logic should mimick Client method -> get_active_events
        current_date = datetime.date.today()
        prev_month = current_date.month - 1
        prev_year = current_date.year
        if prev_month == 0:
            prev_month = 12
            prev_year = prev_year - 1

        if not self.value() or (self.value() == 'Active Outflows'):
            q1 = queryset.filter(
                date_cleared__month=current_date.month, date_cleared__year=current_date.year)
            q2 = queryset.filter(month=prev_month, year=prev_year)
            q3 = queryset.filter(month=current_date.month,
                                 year=current_date.year)
            return q1 | q2 | q3

        if self.value() == 'Past Outflows':
            current_date = datetime.date.today()
            q1 = queryset.exclude(
                date_cleared__month=current_date.month, date_cleared__year=current_date.year)
            q2 = queryset.exclude(month=prev_month, year=prev_year)
            q3 = queryset.exclude(month=current_date.month,
                                  year=current_date.year)
            return q1 & q2 & q3
