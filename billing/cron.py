from .models import Event, Ledger, Cash, Client, CashOutflow, CashInflow, Package, AddOn, TeamMember
from django.conf import settings
import datetime
import logging
from django.db import transaction
import random


def update_event_status():
    q1 = Event.objects.filter(event_status=Event.EventStatus.PROSPECTIVE)
    q2 = Event.objects.filter(event_status=Event.EventStatus.CONFIRMED)
    q3 = Event.objects.filter(payment_status=Event.PaymentStatus.NONE)

    events = q1 | q2 | q3
    for event in events:
        if datetime.date.today() >= event.date:
            if event.payment_status == Event.PaymentStatus.NONE:
                event.event_status = Event.EventStatus.SHELVED
            else:
                event.event_status = Event.EventStatus.COMPLETED
        else:
            if event.payment_status == 'N':
                event.event_status = Event.EventStatus.PROSPECTIVE
            else:
                event.event_status = Event.EventStatus.CONFIRMED
        event.save()
# Cron job for new ledger at start of month


def create_new_ledger():
    month = datetime.date.today().month
    year = datetime.date.today().year
    cash = Cash.objects.get(id=settings.CASH_ID)
    # Setting end of month balance
    previous_month = month
    previous_year = year
    if previous_month == 1:
        previous_month = 12
        previous_year = year-1
    previous_ledger = Ledger.objects.get(
        month=previous_month, year=previous_year)
    previous_ledger.end_balance = cash.cash
    previous_ledger.save()
    # -----------------------------

    if not Ledger.objects.filter(month=month, year=year).exists():
        new_ledger = Ledger(cash=Ledger.cash, month=month, year=year)
        new_ledger.save()


def update_dummy_data():
    month = datetime.date.today().month
    year = datetime.date.today().year

    num_of_clients = random.randint(2, 10)
    num_of_events = random.randint(1, 3)
    num_of_cash_inflows = random.randint(1, num_of_events)
    num_of_cash_outflows = random.randint(3, 6)

    # Create dummy clients
    with transaction.atomic():
        clients = []
        for _ in range(num_of_clients):
            client = Client.objects.create(
                full_name=f'Client {_}',
                phone_number=f'{random.randint(1000000000, 9999999999)}'
            )
            clients.append(client)

        # Create dummy events
        for _ in range(num_of_events):
            client = random.choice(clients)
            event = Event.objects.create(
                client=client,
                package=random.choice(Package.objects.all()
                                      ) if Package.objects.exists() else None,
                event_type=random.choice([choice[0]
                                          for choice in Event.EventType.choices]),
                date=datetime.date.today() - datetime.timedelta(days=random.randint(60, 70)),
                venue=f'Venue {_}',
                discount=random.randint(0, 1000),
            )
            event.lead_photographers.set(TeamMember.objects.all()[
                :random.randint(1, 3)])
            event.add_ons.set(AddOn.objects.all()[:random.randint(0, 5)])
            event.save()

        # Create dummy cash inflows
        for _ in range(num_of_cash_inflows):
            client = random.choice(clients)
            pending_payment = client.get_pending_payment()
            if pending_payment > 0:
                CashInflow.objects.create(
                    source=client,
                    amount=random.randint(
                        1000, pending_payment) if pending_payment > 1000 else pending_payment,
                )

        # Create dummy cash outflows
        sources = ['Rent', 'Equipment Purchase', 'Utilities', 'Misc']
        for _ in range(num_of_cash_outflows):
            CashOutflow.objects.create(
                source=random.choice(sources),
                month=month,
                year=year,
                amount=random.randint(500, 15000),
            )
