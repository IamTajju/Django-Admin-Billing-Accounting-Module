from django.dispatch import receiver
from django.db.models.signals import pre_save, m2m_changed, post_save, pre_delete, post_delete
from billing.models import *

# Helpers


def get_instance_ledger(date):
    ledger = ""
    cash = Cash.objects.get(id=settings.CASH_ID)
    if Ledger.objects.filter(month=date.month, year=date.year).exists():
        ledger = Ledger.objects.get(
            month=date.month, year=date.year)
    else:
        ledger = Ledger(cash=cash, revenue=0, cogs=0, advance_received=0,
                        month=date.month, year=date.year)
        ledger.save()
    return ledger


# CashOutflow

@receiver(post_save, sender=CashOutflow)
def add_outflow_to_ledger(sender, instance, **kwargs):
    date = datetime.date(instance.year, instance.month, 1)
    ledger = get_instance_ledger(date)
    if instance.is_payroll:
        ledger.pay_cogs(instance.amount)
    else:
        ledger.pay_expense(instance.amount)


@receiver(pre_save, sender=CashOutflow)
@receiver(pre_delete, sender=CashOutflow)
def remove_previous_outflow_from_ledger(sender, instance, **kwargs):
    if instance.id is not None:
        previous_outflow_instance = CashOutflow.objects.get(id=instance.id)
        previous_date = datetime.date(
            previous_outflow_instance.year, previous_outflow_instance.month, 1)
        previous_ledger = get_instance_ledger(previous_date)

        if previous_outflow_instance.is_payroll:
            previous_ledger.pay_cogs(int(-previous_outflow_instance.amount))
        else:
            previous_ledger.pay_expense(int(-previous_outflow_instance.amount))


@receiver(pre_save, sender=CashOutflow)
def update_outflow2tbill_based_on_payroll(sender, instance, **kwargs):
    if instance.id is not None:
        previous_outflow_instance = CashOutflow.objects.get(id=instance.id)
        if previous_outflow_instance.is_payroll:
            team_member = TeamMember.objects.get(
                user=User.objects.get(username=instance.source))

            team_member_bill = TeamMemberBill.objects.get(
                team_member=team_member, month=previous_outflow_instance.month, year=previous_outflow_instance.year)

            outflow_tbill_instance = OutflowToTeamMemberBill.objects.get(
                cash_outflow=previous_outflow_instance.id, team_member_bill=team_member_bill.id, month=team_member_bill.month, year=team_member_bill.year)

            outflow_tbill_instance.cleared_amount = instance.amount
            outflow_tbill_instance.save()


# TeamMemberBill

@receiver(post_save, sender=TeamMemberBill)
def create_outflow2tbill_and_payroll_instance(sender, instance, created, **kwargs):
    payroll_instance = CashOutflow(source=str(
        instance.team_member.user.username), month=instance.month, year=instance.year, date_cleared=None)
    payroll_instance.save()
    instance.create_outflow2tbill_instance(payroll_instance)


@receiver(pre_save, sender=TeamMemberBill)
def delete_outflow2tbill_and_payroll_instance(sender, instance, **kwargs):
    if instance.id:
        team_member_bill_instance = TeamMemberBill.objects.get(id=instance.id)
        outflow_tbill_instance = OutflowToTeamMemberBill.objects.get(
            team_member_bill=team_member_bill_instance, month=team_member_bill_instance.month, year=team_member_bill_instance.year)
        outflow_tbill_instance.cash_outflow.delete()
        outflow_tbill_instance.delete()


# CashInflow

@receiver(post_save, sender=CashInflow)
def add_inflow_to_ledger(sender, instance, **kwargs):
    ledger = get_instance_ledger(instance.date)
    ledger.receive_advance(instance.amount)


@receiver(pre_save, sender=CashInflow)
@receiver(pre_delete, sender=CashInflow)
def remove_previous_inflow_from_ledger(sender, instance, **kwargs):
    if instance.id:
        cash_inflow_instance = CashInflow.objects.get(id=instance.id)
        ledger = get_instance_ledger(cash_inflow_instance.date)
        ledger.receive_advance(-cash_inflow_instance.amount)


@receiver(pre_save, sender=CashInflow)
@receiver(pre_delete, sender=CashInflow)
def delete_inflow2event(sender, instance, **kwargs):
    if instance.id:
        cash_inflow_instance = CashInflow.objects.get(id=instance.id)
        cash_inflow_instance.remove_inflow_to_event_instances()


@receiver(post_save, sender=CashInflow)
def create_inflow2event(sender, instance, **kwargs):
    instance.source.make_payment(instance)

# Event


@receiver(post_save, sender=Event)
def add_revenue_to_ledger(sender, instance, **kwargs):
    ledger = get_instance_ledger(instance.date)
    ledger.add_revenue(instance.get_total_budget())


@receiver(pre_save, sender=Event)
@receiver(pre_delete, sender=Event)
def remove_previous_revenue_to_ledger(sender, instance, **kwargs):
    if instance.id:
        event = Event.objects.get(id=instance.id)
        previous_amount = event.get_total_budget()
        previous_ledger = get_instance_ledger(event.date)
        previous_ledger.add_revenue(-(previous_amount))


# Many To Many Relationships being handled here

def add_add_ons_revenue_to_ledger(sender, instance, action, **kwargs):
    instance_ledger = get_instance_ledger(instance.date)
    total_budget = instance.get_total_budget()
    revenue_adjustments = {
        "pre_add": -total_budget,
        "post_add": total_budget,
        "pre_remove": -total_budget,
        "post_remove": total_budget,
        "pre_clear": -total_budget,
        "post_clear": total_budget,
    }
    revenue_adjustment = revenue_adjustments.get(action, 0)
    instance_ledger.add_revenue(revenue_adjustment)


def add_events_to_outflow2bill(sender, instance, action, **kwargs):
    outflow_tbill_instance = OutflowToTeamMemberBill.objects.get(
        team_member_bill=instance, month=instance.month, year=instance.year)

    total_bill = instance.get_total_bill()

    amount_adjustments = {
        "pre_add": -total_bill,
        "post_add": total_bill,
        "pre_remove": -total_bill,
        "post_remove": total_bill,
        "pre_clear": -total_bill,
        "post_clear": total_bill,
    }

    amount_adjustment = amount_adjustments.get(action, 0)
    outflow_tbill_instance.add_amount(amount_adjustment)


m2m_changed.connect(add_events_to_outflow2bill,
                    sender=TeamMemberBill.events.through)
m2m_changed.connect(add_add_ons_revenue_to_ledger,
                    sender=Event.add_ons.through)
