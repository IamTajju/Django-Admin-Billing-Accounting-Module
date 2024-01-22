from .models import Event, Ledger, Cash
from django.conf import settings
import datetime
import logging


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
