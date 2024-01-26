from django.db import models
from user.models import *
import datetime
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum, Value, F, ExpressionWrapper, Min, Value, CharField, Func, Q, OuterRef, Subquery, DateTimeField
from django.db.models.functions import Coalesce, Cast, Replace
from billing.helpers import get_prev_month_year


class Client(models.Model):
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    date_added = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_latest_pk(cls):
        try:
            return cls.objects.latest('id').pk
        except:
            return None

    def __str__(self):
        return self.full_name

    def get_all_events(self):
        return Event.objects.filter(client=self)

    def get_inactive_events(self):
        past_events = [event.id for event in self.get_all_events(
        ) if not event.is_active_event]
        return Event.objects.filter(id__in=past_events)

    def get_payable_events(self):
        return Event.objects.order_by('date').exclude(payment_status=Event.PaymentStatus.FULL).filter(client=self)

    def get_total_revenue(self):
        return sum(event.get_total_budget() for event in self.get_all_events())

    def get_active_events(self):
        active_events = [event.id for event in self.get_all_events()
                         if event.is_active_event]
        return Event.objects.filter(id__in=active_events)

    def make_payment(self, inflow_instance):
        events = self.get_payable_events()
        payment = inflow_instance.amount
        for event in events:
            amount = min(payment, event.get_due())
            event.receive_payment(amount)
            inflow_to_event_instance = InflowToEvent(
                inflow=inflow_instance, event=event, amount=amount)
            inflow_to_event_instance.save()
            payment -= amount
            if payment <= 0:
                break

    def get_pending_payment(self):
        return sum(event.get_due() for event in self.get_payable_events())

    def generate_bill(self, user):
        # events = self.get_active_events() if self.get_active_events(
        # ).exists() else self.get_inactive_events()
        events = self.get_all_events()
        bill = Bill.objects.create(
            client=self, user=user, date=datetime.datetime.now())
        bill.save()
        bill.add_purchase_items(events)
        return bill.id


class Package(models.Model):
    name = models.CharField(max_length=250)
    active = models.BooleanField(default=True)

    class Coverage(models.TextChoices):
        VENUE_ONLY = 'V', _('Venue Only')
        BEFORE_AND_VENUE = 'BV', _('Before + Venue')
        BEFORE_AND_VENUE_AND_AFTER = 'BVA', _('Before + Venue + After')

    details = models.CharField(
        max_length=250, default='200 4R, 30 6L, 3 8R prints', blank=False)
    coverage = models.CharField(max_length=250, choices=Coverage.choices)
    budget = models.PositiveIntegerField(default=0)
    num_photographer = models.PositiveIntegerField(default=0)
    num_cinematographer = models.PositiveIntegerField(default=0)
    time = models.IntegerField(default=5)

    def __str__(self):
        return self.name

    def get_qty_sold(self):
        return Event.objects.filter(package=self).count()

    class Meta:
        verbose_name_plural = "Event Packages"


class AddOn(models.Model):
    name = models.CharField(max_length=250)
    price = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name + "-" + str(self.price) + "Tk"

    def get_qty_sold(self):
        return Event.objects.filter(add_ons=self).count()

    def clean(self):
        if self.pk:
            prev_instance = AddOn.objects.get(pk=self.pk)
            if prev_instance.price != self.price:
                raise ValidationError(
                    "The price field cannot be edited after creation")

    class Meta:
        verbose_name_plural = "Add Ons"


class Event(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, related_name="event", default=Client.get_latest_pk)
    package = models.ForeignKey(
        Package, on_delete=models.CASCADE, null=True, blank=True)

    class EventType(models.TextChoices):
        HOLUD = 'H', _('Holud')
        MEHEDI = 'M', _('Mehedi')
        ENGAGEMENT = 'E', _('Engagement')
        AKDH = 'A', _('Akdh')
        WEDDING = 'WE', _('Wedding')
        WALIMA = "WA", _('Walima')
        BRIDAL_SHOWER = "BS", _("Bridal Shower")
        BIRTHDAY = "BD", _("Birthday")
        NIKKAH = "N", _("Nikkah")
        AIBURO_BHAAT = "AB", _("Aiburo Bhaat")
        SANGEET = "S", _("Sangeet")
        BIYE = "B", _("Biye")
        BASIBIYE = "BB", _("Basibiye")
        BIDAY = "BY", _("Biday")
        WEDDING_RECEPTION = "WR", _("Wedding Reception")
        RECEPTION = "R", _("Reception")
        BOSTRALONGKAR = "BT", _("Bostralongkar")
        DODHIMANGAL = "DM", _("Dodhimangal")
        FAMILY_GET_TOGETHER = "FGT", _('Family Get Together')
        ANNIVERSARY = "AV", _("Anniversary")
        COUPLE_SHOOT = "CS", _("Couple Shoot")
        CORPORATE_EVENT = "CE", _("Corporate Event")
        FAMILY_PHOTOGRAPHY = "FP", _("Family Photography")
        PROPOSAL_EVENT = "PE", _("Proposal Event")
        DALA_EXCHANGE = "DE", _("Dala Exchange")
        OTHERS = 'O', _("Others")

    event_type = models.CharField(max_length=250, choices=EventType.choices)
    add_ons = models.ManyToManyField(
        AddOn, blank=True, verbose_name='Add Ons', related_name="event")
    date = models.DateField(blank=False, null=False)
    venue = models.CharField(max_length=200)
    # auto updates with payment received and date

    class EventStatus(models.TextChoices):
        PROSPECTIVE = 'PR', _('Prospective')
        CONFIRMED = 'C', _('Confirmed')
        COMPLETED = 'D', _('Completed')
        SHELVED = 'S', _('SHELVED')

    event_status = models.CharField(
        max_length=100, choices=EventStatus.choices, default=EventStatus.PROSPECTIVE, editable=False)
    payment_received = models.IntegerField(default=0, editable=False)
    # auto updates with payment received
    discount = models.PositiveIntegerField(default=0)
    lead_photographers = models.ManyToManyField(
        TeamMember, blank=True, verbose_name='Event Lead(s)')

    class PaymentStatus(models.TextChoices):
        NONE = 'N', _('None')
        PARTIAL = 'P', _('Partial')
        FULL = 'F', _('Full')

    payment_status = models.CharField(
        max_length=50, choices=PaymentStatus.choices, default=PaymentStatus.NONE, editable=False)

    @property
    def is_active_event(self):
        current_date = datetime.date.today()
        if self.date < current_date:
            if self.event_status == 'D' and self.payment_status == 'F' and self.date.month != current_date.month:
                return False
        return True

    def get_total_budget(self):
        total_budget = 0
        for add_on in self.add_ons.all():
            total_budget = total_budget + add_on.price
        package_budget = 0
        if self.package:
            package_budget = self.package.budget

        return (total_budget + package_budget - self.discount)

    def get_due(self):
        return self.get_total_budget() - self.payment_received

    def receive_payment(self, payment):
        self.payment_received = self.payment_received + payment
        payment_status_map = {
            (True, True): Event.PaymentStatus.NONE,
            (True, False): Event.PaymentStatus.PARTIAL,
            (False, False): Event.PaymentStatus.FULL,
            (False, True): Event.PaymentStatus.NONE,
        }
        event_status_map = {
            (True, Event.PaymentStatus.NONE): Event.EventStatus.SHELVED,
            (True, Event.PaymentStatus.PARTIAL): Event.EventStatus.COMPLETED,
            (True, Event.PaymentStatus.FULL): Event.EventStatus.COMPLETED,
            (False, Event.PaymentStatus.NONE): Event.EventStatus.PROSPECTIVE,
            (False, Event.PaymentStatus.PARTIAL): Event.EventStatus.CONFIRMED,
            (False, Event.PaymentStatus.FULL): Event.EventStatus.CONFIRMED,
        }

        self.payment_status = payment_status_map.get(
            ((self.payment_received < self.get_total_budget()), (self.payment_received == 0)))
        self.event_status = event_status_map.get(
            ((self.date < datetime.date.today()), self.payment_status))
        self.save()
        return self.payment_received

    def get_leads(self):
        return self.lead_photographers.all()

    def get_photographers(self):
        return self.photographer.all()

    def get_claim_conflicts(self):
        conflicts = []
        num_photographers = 0
        num_cinematographers = 0

        for team_member_bill in self.get_photographers():
            if team_member_bill.team_member.role == 'P':
                num_photographers = num_photographers + 1
            if team_member_bill.team_member.role == 'C':
                num_cinematographers = num_cinematographers + 1

        if self.package:
            if self.package.num_photographer < num_photographers:
                conflicts.append(
                    f"{num_photographers - self.package.num_photographer} extra photographer(s)")

            if self.package.num_cinematographer < num_cinematographers:
                conflicts.append(
                    f"{num_cinematographers - self.package.num_cinematographer} extra cinematographer(s)")
        if len(conflicts) == 0:
            conflicts = ["No conflicts found."]
        return conflicts

    # Estimated Cost
    def get_cost(self):
        cost = 0
        for team_member_bill in self.get_photographers():
            if User.objects.filter(id=team_member_bill.team_member.user.id).exists():
                cost = cost + TeamMember.objects.get(
                    user=User.objects.get(id=team_member_bill.team_member.user.id)).payment_per_event
        return cost

    def __str__(self):
        if self.package:
            return str(self.client) + " - " + str(self.get_event_type_display()) + " | " + str(self.package.name) + " | " + str(self.date.strftime("%d/%m/%y"))
        else:
            return str(self.client) + " - " + str(self.get_event_type_display()) + " | Custom | " + str(self.date.strftime("%d/%m/%y"))

    class Meta:
        ordering = ('date',)


class CashInflow(models.Model):
    source = models.ForeignKey(
        Client, on_delete=models.CASCADE, default=Client.get_latest_pk)
    amount = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True, null=True)

    @property
    def is_active(self):
        current_date = datetime.date.today()
        if self.date.date() < current_date:
            if self.date.month != current_date.month:
                return False
        return True

    def __str__(self) -> str:
        return str(self.source) + "-" + str(self.amount) + "-" + str(self.date)

    def get_all_inflow_to_event_instance(self):
        return InflowToEvent.objects.filter(inflow=self)

    def get_current_state_all_events_budget(self):
        budget = 0
        for instance in self.get_all_inflow_to_event_instance():
            budget = budget + instance.event.get_total_budget()
        return budget

    def remove_inflow_to_event_instances(self):
        for instance in self.get_all_inflow_to_event_instance():
            instance.event.receive_payment(-instance.amount)
        self.get_all_inflow_to_event_instance().delete()

    def save(self, *args, **kwargs):
        # For editing instance only
        # if self.id:
        #     if not self.is_active:
        #         raise Exception("Permanent record. Cannot be changed.")
        # if self.get_current_state_all_events_budget() < self.amount:
        #     raise Exception(
        #         "The new amount is greater than all the associated events' budget combined")

        # # For new instance only
        # else:
        #     pending_payment = self.source.get_pending_payment()
        #     if pending_payment < self.amount:
        #         raise Exception(
        #             f"Cash Inflow amount for client {self.source.full_name} is greater than the pending payment of {pending_payment}")

        return super(CashInflow, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-date',)


class Cash(models.Model):
    cash = models.IntegerField(default=0, verbose_name="Cash In Hand")

    def __str__(self):
        return str(self.cash)


class Ledger(models.Model):
    cash = models.ForeignKey(Cash, on_delete=models.CASCADE)
    end_balance = models.IntegerField(default=0, editable=False)
    revenue = models.IntegerField(default=0)
    cogs = models.IntegerField(
        default=0, verbose_name="Cost of Human Resource")
    expenses = models.IntegerField(
        default=0, verbose_name="Overhead Expenses")
    advance_received = models.IntegerField(default=0)
    month = models.PositiveIntegerField(
        default=datetime.date.today().month, editable=False)
    year = models.PositiveIntegerField(
        default=datetime.date.today().year, editable=False)

    @property
    def cash_balance(self):
        date = datetime.date.today()
        instance_date = datetime.date(
            self.year, self.month, 1) + datetime.timedelta(days=31)
        if instance_date < date:
            return self.end_balance
        return self.cash.cash

    @property
    def gross_profit(self):
        return self.revenue - self.cogs

    @property
    def net_profit(self):
        return self.gross_profit - self.expenses

    def get_ledger_instances_between_now_and_then(self):
        ledger_instances = Ledger.objects.filter(
            year__gte=self.year,
            year__lte=datetime.date.today().year
        ).exclude(
            Q(year=self.year, month__lte=self.month) |
            Q(year=datetime.date.today().year,
              month__gte=datetime.date.today().month)
        )
        return ledger_instances

    def cash_inflow(self, amount):
        self.cash.cash = self.cash.cash + amount
        self.end_balance = self.end_balance + amount
        for ledger_instance in self.get_ledger_instances_between_now_and_then():
            ledger_instance.end_balance += amount
            ledger_instance.save()
        self.cash.save()
        return self.cash.cash

    def cash_outflow(self, amount):
        self.cash.cash = self.cash.cash - amount
        self.end_balance = self.end_balance - amount
        self.cash.save()
        for ledger_instance in self.get_ledger_instances_between_now_and_then():
            ledger_instance.end_balance -= amount
            ledger_instance.save()
        self.save()
        return self.cash.cash

    def receive_advance(self, amount):
        self.cash_inflow(amount)
        self.advance_received += amount
        self.save()

    def add_revenue(self, amount):
        self.revenue = self.revenue + amount
        self.save()

    def pay_expense(self, amount):
        self.cash_outflow(amount)
        self.expenses = self.expenses + amount
        self.save()

    def pay_cogs(self, amount):
        self.cash_outflow(amount)
        self.cogs = self.cogs + amount
        self.save()

    def __str__(self):
        return str(self.month) + "-" + str(self.year)

    class Meta:
        ordering = ('year', 'month',)


class TeamMemberBill(models.Model):
    class Meta:
        verbose_name_plural = "Team member bills"
        # Will work on postgress DB, this is a DB-level action, SQLite doesn't support it
        # unique_together = ('team_member', 'month', 'year',)

    team_member = models.ForeignKey(
        TeamMember, on_delete=models.CASCADE, editable=False)
    events = models.ManyToManyField(Event, related_name="photographer")
    month = models.PositiveIntegerField(
        default=get_prev_month_year()[0])
    year = models.PositiveIntegerField(
        default=get_prev_month_year()[1])
    adjustment = models.IntegerField(default=0)
    comment = models.CharField(max_length=1000, blank=True)

    @property
    def cleared(self):
        try:
            print(OutflowToTeamMemberBill.objects.get(
                team_member_bill=self, month=self.month, year=self.year).cleared_amount)
            if OutflowToTeamMemberBill.objects.get(team_member_bill=self, month=self.month, year=self.year).cleared_amount > 0:
                return True
            return False
        except:
            return False

    def get_total_events(self):
        return len(self.events.all())

    def __str__(self):
        return str(self.team_member) + "-" + str(datetime.datetime.strptime(str(self.month), "%m").strftime("%B"))

    def get_total_bill(self):
        return (self.team_member.payment_per_event * self.get_total_events()) + self.adjustment

    def create_outflow2tbill_instance(self, outflow_instance):
        outflow_tbill_instance = OutflowToTeamMemberBill(
            team_member_bill=self, cash_outflow=outflow_instance, amount=self.get_total_bill(), month=self.month, year=self.year, cleared_amount=0)
        outflow_tbill_instance.save()

    def save(self, *args, **kwargs):
        if self.id:
            if self.cleared:
                raise Exception(
                    f"TeammemberBill already cleared for {self.month}-{self.year}")
        return super(TeamMemberBill, self).save(*args, **kwargs)


class CashOutflow(models.Model):
    # This might store ID for for event listing as foreign key, will need to convert to int when making foreign key queries
    source = models.CharField(max_length=250)
    month = models.PositiveIntegerField(
        default=datetime.date.today().month)
    year = models.PositiveIntegerField(
        default=datetime.date.today().year)
    # Actual amount to be added to ledger
    amount = models.PositiveIntegerField(default=0, blank=False)
    date_cleared = models.DateField(
        default=datetime.date.today(), blank=True, null=True)

    @property
    def is_payroll(self):
        if User.objects.filter(username=self.source).exists():
            return True
        return False

    @property
    def is_active(self):
        current_date = datetime.date.today()
        if self.date_cleared and self.date_cleared < current_date and self.date_cleared.month != current_date.month:
            return False
        return True

    class Meta:
        ordering = ('year', 'month', 'date_cleared')

    def save(self, *args, **kwargs):
        if self.id:
            if not self.is_active:
                raise Exception("Permanent record. Cannot be changed.")
        return super(CashOutflow, self).save(*args, **kwargs)


class Bill(models.Model):
    class Meta:
        verbose_name_plural = "Historical Bills"

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, related_name='bill')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(null=True)

    def add_purchase_items(self, events):
        grouped_events = events.exclude(package=None).values(
            'package').annotate(count=Count('id'))
        grouped_add_ons = events.exclude(package=None).values(
            'add_ons').annotate(count=Count('id'))
        custom_events = events.filter(package=None)

        for package in grouped_events:
            package_events = events.filter(package=package['package'])
            purchase = Purchase.objects.create(
                bill=self, package=Package.objects.get(id=package['package']))
            purchase.quantity = package['count']
            for event in package_events:
                purchase.append_date(
                    event.date, event.get_event_type_display())
                purchase.discount += event.discount
                purchase.append_leads(event.lead_photographers.all())

            purchase.save()

        for add_on in grouped_add_ons:
            if add_on['add_ons'] is not None:
                add_on_purchase = AddOnPurchase.objects.create(
                    bill=self, add_on=AddOn.objects.get(id=add_on['add_ons']), quantity=add_on['count'])
                add_on_purchase.price = add_on_purchase.add_on.price * add_on_purchase.quantity
                add_on_purchase.save()

        for custom_event in custom_events:
            price = custom_event.add_ons.through.objects.filter(
                event=custom_event).aggregate(total=Coalesce(Sum('addon__price'), Value(0)))['total']
            add_ons = custom_event.add_ons.all().values('name').annotate(count=Count('id'))
            details = '\n'.join(
                [f"{item['name']}" for item in add_ons])
            # dates field also holds the event_type data, didn't change name because will require migration in production
            custom_purchase = CustomPurchase.objects.create(
                bill=self, date=f"{custom_event.get_event_type_display()} - {custom_event.date}", details=details, price=price)
            custom_purchase.discount = custom_event.discount
            custom_purchase.leads.set(custom_event.lead_photographers.all())
            custom_purchase.save()

    def __str__(self):
        return str(self.client) + "-" + str(self.date)

    def get_invoice_number(self):
        return "INV" + str(self.id)

    def get_subtotal(self):
        purchase_total = Purchase.objects.filter(bill=self).annotate(total=ExpressionWrapper(
            F('package__budget') * F('quantity'), output_field=models.IntegerField())).aggregate(total_amount=Coalesce(Sum('total'), Value(0)))['total_amount']
        custom_purchase_total = CustomPurchase.objects.filter(
            bill=self).aggregate(total=Coalesce(Sum('price'), Value(0)))['total']

        return purchase_total + custom_purchase_total

    def get_add_ons_total(self):
        return AddOnPurchase.objects.filter(bill=self).annotate(total=ExpressionWrapper(F('add_on__price') * F('quantity'), output_field=models.IntegerField())).aggregate(total_amount=Coalesce(Sum('total'), Value(0)))['total_amount']

    def get_discount(self):
        return Purchase.objects.filter(bill=self).aggregate(total=Coalesce(Sum('discount'), Value(0)))['total'] + CustomPurchase.objects.filter(bill=self).aggregate(total=Coalesce(Sum('discount'), Value(0)))['total']

    def get_total(self):
        return self.get_subtotal() + self.get_add_ons_total() - self.get_discount()

    def get_due(self):
        return Client.objects.get(bill=self).get_pending_payment()

    def get_paid(self):
        return self.get_total() - self.get_due()

    def get_purchase_list(self):
        purchases = Purchase.objects.filter(bill=self)

        # Sort the queryset in Python based on the first_date property
        sorted_purchases = sorted(
            purchases, key=lambda purchase: purchase.first_date)

        return sorted_purchases

    def get_custom_purchase_list(self):
        custom_purchases = CustomPurchase.objects.filter(bill=self)

        # Sort the queryset in Python based on the first_date property
        sorted_purchases = sorted(
            custom_purchases, key=lambda custom_purchase: custom_purchase.first_date)

        return sorted_purchases

    def is_custom_second(self):
        custom_purchases = self.get_custom_purchase_list()
        standard_purchases = self.get_purchase_list()

        if custom_purchases and standard_purchases:
            return custom_purchases[0].first_date > standard_purchases[0].first_date

        # Handle cases where either list is empty
        return False

    def get_add_ons_list(self):
        return AddOnPurchase.objects.filter(bill=self)


class Purchase(models.Model):
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, null=True, related_name='purchase')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, null=True)
    # dates field also holds the event_type data, didn't change name because will require migration in production
    dates = models.TextField()
    leads = models.ManyToManyField(TeamMember, blank=True)
    discount = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)

    @property
    def first_date(self):
        # Split the string by '&' to separate the date parts
        date_parts = self.dates.split('&')

        # Initialize a variable to store the earliest date
        earliest_date = None

        for date_part in date_parts:
            # Split each date part by '-' to get the date string
            date_str = date_part.split(' - ')[-1].strip()
            print(date_str)
            # Parse the date string into a datetime object
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

            # Update the earliest_date if it's None or the current date is earlier
            if earliest_date is None or date < earliest_date:
                earliest_date = date

        if earliest_date is not None:
            return earliest_date.date()
        else:
            return None

    def append_date(self, date, event_type):
        self.dates = str(event_type) + ' - ' + str(
            date) if not self.dates else f"{self.dates} & {str(event_type)} - {str(date)}"

    def append_leads(self, leads):
        unique_leads = set(leads)
        current_leads = set(self.leads.all())
        self.leads.set(unique_leads.union(current_leads))


class CustomPurchase(models.Model):
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, null=True, related_name='custom_purchase')
    details = models.TextField()
    date = models.TextField()
    leads = models.ManyToManyField(TeamMember, blank=True)
    price = models.IntegerField()
    discount = discount = models.IntegerField(default=0)

    @property
    def first_date(self):
        # Split the string by '&' to separate the date parts
        date_parts = self.date.split('&')

        # Initialize a variable to store the earliest date
        earliest_date = None

        for date_part in date_parts:
            # Split each date part by '-' to get the date string
            date_str = date_part.split(' - ')[-1].strip()

            # Parse the date string into a datetime object
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

            # Update the earliest_date if it's None or the current date is earlier
            if earliest_date is None or date < earliest_date:
                earliest_date = date

        if earliest_date is not None:
            return earliest_date.date()
        else:
            return None


class AddOnPurchase(models.Model):
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, null=True, related_name="add_ons")
    add_on = models.ForeignKey(AddOn, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=0)


class InflowToEvent(models.Model):
    inflow = models.ForeignKey(
        CashInflow, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)


class InflowToBill(models.Model):
    inflow = models.ForeignKey(
        CashInflow, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.inflow}"


class OutflowToTeamMemberBill(models.Model):
    team_member_bill = models.ForeignKey(
        TeamMemberBill, on_delete=models.CASCADE)
    cash_outflow = models.ForeignKey(
        CashOutflow, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    month = models.PositiveIntegerField(
        default=datetime.date.today().month)
    year = models.PositiveIntegerField(
        default=datetime.date.today().year)
    cleared_amount = models.IntegerField(default=0)

    def add_amount(self, amount):
        self.amount = self.amount + amount
        self.save()
