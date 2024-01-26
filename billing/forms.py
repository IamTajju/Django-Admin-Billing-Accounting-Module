from django import forms
from .models import Client, CashInflow, Event, Package, TeamMemberBill
from .business_logic import services, validators


class InflowForm(forms.ModelForm):
    class Meta:
        model = CashInflow
        fields = ('source', 'amount')

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
                try:
                    instance = self.instance if self.instance.pk else None
                    cleaned_data = self.cleaned_data
                    cleaned_data['source'] = self.instance.source
                    validators.CashInflowValidator(self.cleaned_data, instance)
                except ValueError as e:
                    raise forms.ValidationError(e)

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
        if self.is_valid():
            try:
                instance = self.instance if self.instance.pk else None
                validators.EventValidator(cleaned_data, instance)

            except ValueError as e:
                raise forms.ValidationError(e)

    def save(self, commit=True):
        instance = super().save(commit=commit)

        if Event.objects.filter(id=instance.pk).exists():
            add_ons_data = self.cleaned_data.pop('add_ons', None)
            lead_photographers_data = self.cleaned_data.pop(
                'lead_photographers', None)

            # Update the fields of the 'Event' model instance with the validated data
            for key, value in self.cleaned_data.items():
                setattr(instance, key, value)

            if add_ons_data is not None:
                instance.add_ons.clear()
                instance.add_ons.add(*add_ons_data)

            if lead_photographers_data is not None:
                instance.lead_photographers.clear()
                instance.lead_photographers.add(*lead_photographers_data)

            services.EventServices(instance, add_ons_data)
            # Save the updated instance

        return instance


