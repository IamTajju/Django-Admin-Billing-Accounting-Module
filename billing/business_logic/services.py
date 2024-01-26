from billing.models import Event, Bill, InflowToBill, Client
from user.models import User
from django.urls import reverse
import datetime

class EventServices():
    def __init__(self, event_instance, add_ons_data):
        self.update_payment_status(event_instance, add_ons_data)
        self.update_event_status(event_instance)


    @classmethod
    def update_event_status(cls, event_instance):
        today = datetime.date.today()

        event_status_map = {
            (True, Event.PaymentStatus.NONE): Event.EventStatus.SHELVED,
            (True, Event.PaymentStatus.PARTIAL): Event.EventStatus.COMPLETED,
            (True, Event.PaymentStatus.FULL): Event.EventStatus.COMPLETED,
            (False, Event.PaymentStatus.NONE): Event.EventStatus.PROSPECTIVE,
            (False, Event.PaymentStatus.PARTIAL): Event.EventStatus.CONFIRMED,
            (False, Event.PaymentStatus.FULL): Event.EventStatus.CONFIRMED,
        }

        event_instance.event_status = event_status_map.get(((event_instance.date < today), event_instance.payment_status))
        return True
    

    @classmethod
    def update_payment_status(cls, event_instance, add_ons_data):
        total_budget = (event_instance.package.budget if event_instance.package else 0) + sum([add_on.price for add_on in add_ons_data] if add_ons_data else [add_on.price for add_on in event_instance.add_ons.all()]) - (event_instance.discount if event_instance else 0)
        
        payment_status_map = {
            (True, True): Event.PaymentStatus.NONE,
            (True, False): Event.PaymentStatus.PARTIAL,
            (False, False): Event.PaymentStatus.FULL,
            (False, True): Event.PaymentStatus.NONE,
        }

        event_instance.payment_status = payment_status_map.get(((event_instance.payment_received < total_budget), (event_instance.payment_received == 0)))
        return event_instance



def create_inflow2bill(cash_inflow_instance, request, from_admin=None):
    client = Client.objects.get(id=cash_inflow_instance.source.id)
    bill_id = client.generate_bill(User.objects.get(id=request.user.id))
    inflow_bill_instance = InflowToBill(
        inflow=cash_inflow_instance, bill_id=bill_id)
    inflow_bill_instance.save()
    invoice_link = str(request.get_host()) + str(reverse("billing:view-bill", args=[
        bill_id]))
    if from_admin:
        return bill_id
    return invoice_link

def edit_inflow2bill(cash_inflow_instance, request, from_admin=None):
    client = Client.objects.get(id=cash_inflow_instance.source.id)
    bill_id = client.generate_bill(
            User.objects.get(id=request.user.id))
    inflow2bill = InflowToBill.objects.get(inflow=cash_inflow_instance.id)
    inflow2bill.bill = Bill.objects.get(id=bill_id)
    inflow2bill.save()
    invoice_link = str(request.get_host()) + str(reverse("billing:view-bill", args=[
        bill_id]))
    
    if from_admin:
        return bill_id
    return invoice_link
