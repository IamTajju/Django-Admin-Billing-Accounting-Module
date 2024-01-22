from django import forms
from billing.models import Client, CashInflow, Event, Package
import logging
import datetime


class InflowForm(forms.ModelForm):
    editing = forms.BooleanField(
        help_text="Tick ONLY if you're editing a previous cash inflow instance.", required=False)

    class Meta:
        model = CashInflow
        fields = ('source', 'amount', 'editing')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'source' in self.fields.keys():
            clients = Client.objects.all()
            for client in clients:
                if len(client.get_active_events()) == 0:
                    clients = clients.exclude(id=client.id)
            self.fields['source'].queryset = clients

    def clean(self):
        if self.is_valid():
            try:
                source = self.cleaned_data['source']
            except:
                cash_inflow_instance = CashInflow.objects.get(
                    id=self.instance.pk)
                amount = self.cleaned_data['amount']
                if cash_inflow_instance.source is not None:
                    client = Client.objects.get(
                        id=cash_inflow_instance.source.id)
                    total_due = 0
                    total_budget = 0
                    for event in client.get_payable_events():
                        total_due = total_due + event.get_due()
                    for event in client.get_active_events():
                        total_budget = total_budget + event.get_total_budget()
                    is_editing = self.cleaned_data.get('editing', None)

                    if amount > total_due and (not is_editing):
                        raise forms.ValidationError(
                            f"Total amount from {cash_inflow_instance.source.full_name} should be less than or equal to BDT {total_due}")
                    if is_editing and (amount > cash_inflow_instance.amount + total_due):
                        raise forms.ValidationError(
                            f"Total amount from {cash_inflow_instance.source.full_name} should be less than or equal to BDT {cash_inflow_instance.amount + total_due}")

        else:
            raise forms.ValidationError("Invalid amount")


class TeamMemberBillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'events' in self.fields.keys():
            self.fields['events'].queryset = Event.objects.exclude(
                date__gte=datetime.date.today())


class EventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'package' in self.fields.keys():
            self.fields['package'].queryset = Package.objects.filter(
                active=True)

    class Meta:
        model = Event
        fields = ('__all__')

    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        if self.is_valid():
            if Event.objects.filter(id=self.instance.pk).exists():
                event_budget = 0
                for add_on in self.cleaned_data['add_ons']:
                    event_budget = event_budget + add_on.price
                package = self.cleaned_data['package']
                if package:
                    event_budget = event_budget + package.budget
                event_instance = Event.objects.get(id=self.instance.pk)
                # Shouldn't the discount be self.cleaned_data['discount']
                event_budget = event_budget - event_instance.discount
                # if event_instance.payment_received > event_budget:
                #     raise forms.ValidationError(
                #         f"The payment received for this event BDT {event_instance.payment_received} is greater than the edited budget of the event BDT {event_budget}. First change the Cash Inflow instance.")
