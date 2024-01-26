from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from billing.models import *
from billing.business_logic.services import create_inflow2bill, edit_inflow2bill
from user.models import TeamMember
from user.models import *
from .serializers import *
import logging
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, authentication, permissions, viewsets
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist

ensure_csrf = method_decorator(ensure_csrf_cookie)


class setCSRFCookie(APIView):
    permission_classes = []
    authentication_classes = []

    @ensure_csrf
    def get(self, request):
        return Response("CSRF Cookie set.")


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        user_data = {"name": user.get_full_name(
        ), "role": user.groups.values_list('name', flat=True)[0]}
        print(user_data)
        return Response(user_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


class ClientPendingPayment(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Client.objects.all()

    def get(self, request):
        clients = []
        for index, client in enumerate(self.queryset.all()):
            row = {}
            row['id'] = client.id
            row['name'] = client.full_name
            row['pending_payment'] = client.get_pending_payment()

            clients.append(row)

        return Response(clients, status=status.HTTP_200_OK)


class ClientTableView(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Client.objects.all().order_by('-id')

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        clients = []
        for index, client in enumerate(self.queryset.all()):
            row = {index: {}}
            row[index]["id"] = client.id
            row[index]["full_name"] = client.full_name
            row[index]["phone_number"] = client.phone_number
            # Protected Cols
            if user.is_superuser or ('Admin',) in user.groups.all().values_list('name'):
                row[index]["total_revenue"] = client.get_total_revenue()
                row[index]["total_pending_payment"] = client.get_pending_payment()
            # --------------------
            row[index]["active_events"] = [{event.id: str(event)}
                                           for event in client.get_active_events()]
            row[index]["past_events"] = [{event.id: str(event)}
                                         for event in client.get_inactive_events()]
            if Bill.objects.filter(client=client).exists():
                bill = Bill.objects.filter(client=client).latest('date')
                row[index]["latest_invoice_link"] = str(request.get_host()) + str(reverse(
                    "billing:view-bill", args=[bill.id]))
            else:
                row[index]["latest_invoice_link"] = None

            # Classifiying for month_year and activity status
            row[index]["status"] = "Active"
            if client.get_active_events().exists():
                row[index]["month_year"] = client.get_active_events().order_by(
                    "date").first().date.strftime('%m-%Y')
            else:
                if not client.get_payable_events().exists():
                    row[index]["status"] = "Inactive"
                if client.get_inactive_events().exists():
                    row[index]["month_year"] = client.get_inactive_events().order_by(
                        "date").first().date.strftime('%m-%Y')
                else:
                    row[index]["month_year"] = None
            clients.append(row)

        return Response(clients, status=status.HTTP_200_OK)


class EventTableView(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Event.objects.all().order_by('-date')
    priviliged = False

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        priviliged = False
        if user.is_superuser or ('Admin',) in user.groups.all().values_list('name'):
            priviliged = True
        events = []
        for index, event in enumerate(self.queryset.all()):
            row = {index: {}}
            row[index]["id"] = event.id
            row[index]["client"] = event.client.full_name
            row[index]["event_type"] = {event.get_event_type_display():
                                        event.event_type}
            if event.package is not None:
                row[index]["package"] = event.package.name
            else:
                row[index]["package"] = "No Package Selected"
            row[index]["add_ons"] = [{"id": add_on.id, "name": add_on.name}
                                     for add_on in event.add_ons.all()]
            # Protected Cols
            if priviliged:
                row[index]["discount"] = event.discount
                row[index]["discount_budget"] = event.get_total_budget()
                row[index]["payment_received"] = event.payment_received
                row[index]["cost"] = event.get_cost()
            # --------------------
            row[index]["date"] = event.date
            row[index]["venue"] = event.venue
            row[index]["lead_by"] = [{"id": lead.id, "name": str(lead)}
                                     for lead in event.lead_photographers.all()]
            row[index]["covered_by"] = [{"id": photographer.id, "name": str(photographer)}
                                        for photographer in event.photographer.all()]

            row[index]["claim_conflict"] = event.get_claim_conflicts()

            row[index]['event_status'] = event.event_status
            row[index]['payment_status'] = event.payment_status
            row[index]['active'] = event.is_active_event
            events.append(row)

        return Response(events, status=status.HTTP_200_OK)


class CashInflowTableView(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = CashInflow.objects.all().order_by('-id')

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        if not (user.is_superuser or (('Admin',) in user.groups.all().values_list('name')) or (('Manager',) in user.groups.all().values_list('name'))):
            return Response(status=status.HTTP_403_FORBIDDEN)
        cashinflows = []
        for index, cashinflow in enumerate(self.queryset.all()):
            row = {"index": index}
            row["id"] = cashinflow.id
            row["source"] = cashinflow.source.full_name
            row['client_id'] = cashinflow.source.id
            row['pending_payment'] = cashinflow.source.get_pending_payment()
            row["amount"] = cashinflow.amount
            row["date"] = cashinflow.date.date()
            if InflowToBill.objects.filter(inflow=cashinflow).exists():
                bill = InflowToBill.objects.get(inflow=cashinflow).bill
                row["invoice_link"] = str(request.get_host()) + str(reverse(
                    "billing:view-bill", args=[bill.id]))
            else:
                row["invoice_link"] = ""
            row['active'] = cashinflow.is_active

            cashinflows.append(row)

        return Response(cashinflows, status=status.HTTP_200_OK)


class HistoricalBillTableView(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Bill.objects.all().order_by('-id')

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        if not (user.is_superuser or ('Admin',) in user.groups.all().values_list('name')):
            return Response(status=status.HTTP_403_FORBIDDEN)
        bills = []
        for index, bill in enumerate(self.queryset.all()):
            row = {"index": index}
            row["id"] = bill.id
            row["client"] = bill.client.full_name
            row["date"] = bill.date.date()
            row["user"] = bill.user.get_full_name()
            row["invoice_link"] = str(request.get_host()) + str(reverse(
                "billing:view-bill", args=[bill.id]))

            bills.append(row)

        return Response(bills, status=status.HTTP_200_OK)


class LedgerTableView(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Ledger.objects.all()

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        if not (user.is_superuser or ('Admin',) in user.groups.all().values_list('name')):
            return Response(status=status.HTTP_403_FORBIDDEN)
        ledgers = []
        for index, ledger in enumerate(self.queryset.all()):
            row = {"index": index}
            row["id"] = ledger.id
            row['month'] = ledger.month
            row['year'] = ledger.year
            row['cash'] = ledger.cash_balance
            row['advance_received'] = ledger.advance_received
            row['revenue'] = ledger.revenue
            row['cost_of_human_resource'] = ledger.cogs
            row['gross_profit'] = ledger.gross_profit
            row['overhead_expenses'] = ledger.expenses
            row['net_profit'] = ledger.net_profit

            ledgers.append(row)

        return Response(ledgers, status=status.HTTP_200_OK)


class PackageTableView(generics.ListAPIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Package.objects.all()
    serializer_class = PackageSerializer


class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class PackageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Package.objects.all()
    serializer_class = PackageSerializer

    @action(detail=False, methods=['GET'])
    def coverage_choices(self, request):
        coverage_choices = [
            {'value': choice[0], 'label': choice[1]}
            for choice in Package.Coverage.choices
        ]
        return Response(coverage_choices)


class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Event.objects.all().order_by('-id')
    serializer_class = EventSerializer

    def update(self, request, *args, **kwargs):
        event = Event.objects.get(id=kwargs['pk'])
        serializer = EventSerializer(
            event, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
        event = serializer.save()
        client = event.client
        invoice_link = str(request.get_host()) + str(reverse("billing:view-bill", args=[
            client.generate_bill(User.objects.get(id=request.user.id))]))
        return Response({'invoice_link': invoice_link}, status=status.HTTP_202_ACCEPTED)


class AddOnViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer


class CashOutflowViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = CashOutflow.objects.all().order_by('-id')
    serializer_class = CashOutflowSerializer

    def list(self, request, *args, **kwargs):
        cash_outflows = []
        for index, cash_outflow in enumerate(self.queryset.all()):
            row = {'index': index}
            row['id'] = cash_outflow.id
            if cash_outflow.is_payroll:
                row['expenses_type'] = "Payroll"
            else:
                row['expenses_type'] = 'Overhead'
            row['source_of_expense'] = cash_outflow.source
            row['month'] = cash_outflow.month
            row['year'] = cash_outflow.year
            row['amount'] = cash_outflow.amount
            row['date_cleared'] = cash_outflow.date_cleared
            row['month_year'] = f"{cash_outflow.month}/{cash_outflow.year}"

            row['is_active'] = cash_outflow.is_active
            if cash_outflow.is_payroll:
                o2tbl_instance = OutflowToTeamMemberBill.objects.get(
                    cash_outflow=cash_outflow, month=cash_outflow.month, year=cash_outflow.year)
                row['related_tbill'] = {'source': o2tbl_instance.team_member_bill.team_member.user.username, 'team_member_bill': str(
                    o2tbl_instance.team_member_bill), 'month': o2tbl_instance.team_member_bill.month, 'year': o2tbl_instance.team_member_bill.year, 'events': [str(event) for event in o2tbl_instance.team_member_bill.events.all()], 'bill_for_events': (o2tbl_instance.team_member_bill.get_total_bill() - o2tbl_instance.team_member_bill.adjustment), 'adjustment': o2tbl_instance.team_member_bill.adjustment, 'comment': o2tbl_instance.team_member_bill.comment, 'total_bill': o2tbl_instance.team_member_bill.get_total_bill()}
            else:
                row['related_tbill'] = None
            cash_outflows.append(row)
        return Response(cash_outflows, status=status.HTTP_200_OK)


class TeamMemberBillViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = TeamMemberBill.objects.all()
    serializer_class = TeamMemberBillSerializer

    def list(self, request, *args, **kwargs):
        # Vars to check if user has add permission
        team_member_bills = [{'can_add': True}]
        user = User.objects.get(id=request.user.id)
        prev_month = datetime.date.today().month - 1
        prev_year = datetime.date.today().year
        if prev_month == 0:
            prev_month = 11 + 1
            prev_year = prev_year - 1

        # Admin gets to see all bills
        if (user.is_superuser or (('Admin',) in user.groups.all().values_list('name'))):
            queryset = TeamMemberBill.objects.all()

        # Specific user gets to see only their bills
        else:
            team_member = TeamMember.objects.get(user=user)
            queryset = TeamMemberBill.objects.filter(
                team_member=team_member.id)

        if queryset.filter(month=prev_month, year=prev_year).exists():
            team_member_bills[0]['can_add'] = False

        for index, team_member_bill in enumerate(queryset.all()):
            row = {"index": index}
            row['id'] = team_member_bill.id
            row['team_member'] = team_member_bill.team_member.user.get_full_name()
            row['month'] = team_member_bill.month
            row['year'] = team_member_bill.year
            row['month_year'] = f"{team_member_bill.month}/{team_member_bill.year}"
            row['covered_events'] = [{"id": event.id, 'event': str(
                event)}for event in team_member_bill.events.all()]

            row['bill_for_events'] = (team_member_bill.get_total_bill())

            row['adjustment'] = team_member_bill.adjustment
            row['comment'] = team_member_bill.comment
            if OutflowToTeamMemberBill.objects.filter(
                    team_member_bill=team_member_bill, month=team_member_bill.month, year=team_member_bill.year).exists():
                row['amount_cleared'] = OutflowToTeamMemberBill.objects.get(
                    team_member_bill=team_member_bill, month=team_member_bill.month, year=team_member_bill.year).cleared_amount
            else:
                row['amount_cleared'] = 'Not cleared yet.'

            row['cleared'] = team_member_bill.cleared

            team_member_bills.append(row)

        return Response(team_member_bills, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        user = User.objects.get(id=request.user.id)
        logging.critical(user)
        try:
            team_member = TeamMember.objects.get(user=user)
        except:
            return Response("This user cannot create team member bills", status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(team_member=team_member)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_dashboard_data(self, request):
        response_data = {"tmember_events": 0, "tmember_earnings": 0,
                         "tmember_claimed": 0, "tmember_prev_events": 0, "recent_events": []}
        try:
            member = TeamMember.objects.get(user=request.user)
            prev_month, prev_year = get_prev_month_year()
            tbill = TeamMemberBill.objects.get(
                team_member=member, month=prev_month, year=prev_year)

            num_of_events = tbill.get_total_events()

            penult_date = date(prev_year, prev_month, 1) - \
                relativedelta(months=1)
            try:
                penult_tbill = TeamMemberBill.objects.get(
                    team_member=member, month=penult_date.month, year=penult_date.year)
                prev_num_of_events = penult_tbill.get_total_events()
            except ObjectDoesNotExist:
                prev_num_of_events = 0

            total_earnings = OutflowToTeamMemberBill.objects.get(
                team_member_bill=tbill, month=tbill.month, year=tbill.year).cleared_amount if tbill.cleared else 0

            start_of_month = date(datetime.now().year, datetime.now().month, 1)
            next_month = start_of_month + relativedelta(months=1)

            recent_events = Event.objects.filter(
                date__gt=start_of_month, date__lte=next_month).order_by('-date')

            recent_events_serialized = RecentEventSerializer(
                recent_events, many=True)
            recent_events_serialized = recent_events_serialized.data

            response_data["tmember_events"] = num_of_events
            response_data["tmember_earnings"] = total_earnings
            response_data["tmember_claimed"] = tbill.get_total_bill()
            response_data["tmember_prev_events"] = prev_num_of_events
            response_data["recent_events"] = recent_events_serialized

        except ObjectDoesNotExist:
            logging.critical("Previous Month Team Member Doesn't Exist.")

        return Response(response_data, status=status.HTTP_200_OK)


class TeamMemberViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer


class CashInflowViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = CashInflow.objects.all()
    serializer_class = CashInflowSerializer

    def create(self, request, *args, **kwargs):
        serializer = CashInflowSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        cash_inflow_instance = serializer.save()
        invoice_link = create_inflow2bill(cash_inflow_instance, request)
        return Response({'invoice_link': invoice_link}, status=status.HTTP_202_ACCEPTED)

    def update(self, request, *args, **kwargs):
        cashinflow = CashInflow.objects.get(id=kwargs['pk'])
        serializer = CashInflowSerializer(
            cashinflow, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)

        invoice_link = edit_inflow2bill(cashinflow, request)
        serializer.save()
        return Response({'invoice_link': invoice_link}, status=status.HTTP_202_ACCEPTED)


class CEARegistration(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Client.objects.all()

    def get(self, request):
        response = {}
        '''
        [{"Event Type Full Name": "Short hand"},{"Holud" : "H"}]
        '''
        response['event_type'] = [{item[0]: item[1]}
                                  for item in Event.EventType._member_map_.items()]

        # Only active packages
        response['package'] = Package.objects.filter(
            active=True).values("id", "name", 'budget')
        response['client'] = Client.objects.all().values("id",
                                                         "full_name")
        response['add_ons'] = AddOn.objects.all(
        ).values("id", "name", "price")

        response['event_leads'] = (TeamMember.objects.filter(role='C') | TeamMember.objects.filter(
            role='P') | TeamMember.objects.filter(role='A')).values("id", "user__first_name")
        return Response(response)

    def post(self, request):
        is_new_client = False
        if type(request.data['client']) == dict:
            client_serializer = ClientSerializer(data=request.data['client'])
            if not client_serializer.is_valid():
                return Response(client_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            client = client_serializer.save()
            is_new_client = True
        elif type(request.data['client']) == int:
            client = Client.objects.get(id=request.data['client'])
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        events = []
        for index, event in enumerate(request.data['events']):
            if event['package'] == None:
                return Response({"error_message": "No package selected", "event_index": index}, status=status.HTTP_400_BAD_REQUEST)

            if event['package'] == 'custom':
                event['package'] = None

            add_ons_list = []
            for add_on in event['additions']:
                if type(add_on) == dict:
                    add_ons_serializer = AddOnSerializer(
                        data=add_on)
                    if not add_ons_serializer.is_valid():
                        if is_new_client:
                            client.delete()
                        return Response(add_ons_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    add_ons = add_ons_serializer.save()
                    add_ons_list.append(add_ons.id)
                elif type(add_on) == int:
                    add_ons_list.append(add_on)
                else:
                    if is_new_client:
                        client.delete()
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            event['add_ons'] = add_ons_list
            event_serializer = EventSerializer(data=event)
            try:
                if event_serializer.is_valid():
                    saved_event = event_serializer.save(client=client)
                    events.append(saved_event)
                else:
                    errors = event_serializer.errors
                    print()
                    errors.update({"event_index": index})
                    if is_new_client:
                        client.delete()
                    for e in events:
                        e.delete()
                    return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as error:
                logging.critical(error)
                if is_new_client:
                    client.delete()
                for e in events:
                    e.delete()
                return Response({"error_message": str(error), "event_index": index}, status=status.HTTP_400_BAD_REQUEST)

        if request.data['cash_inflow'] > 0:
            cash_inflow_serializer = CashInflowSerializer(
                data={'source': client.pk, 'amount': request.data['cash_inflow']})
            if cash_inflow_serializer.is_valid():
                cash_inflow_serializer.save()
            else:
                logging.critical(cash_inflow_serializer.errors)
                if is_new_client:
                    client.delete()
                else:
                    for e in events:
                        e.delete()
                return Response(cash_inflow_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invoice_link = str(request.get_host()) + str(reverse("billing:view-bill", args=[
            client.generate_bill(User.objects.get(id=request.user.id))]))
        return Response({'invoice_link': invoice_link}, status=status.HTTP_201_CREATED)


class LastYearFinancialSummary(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Ledger.objects.all()

    def get_month_name(self, month_number):
        return datetime(2022, month_number, 1).strftime('%b')

    def get_financial_data(self, month, year):
        try:
            ledger = Ledger.objects.get(month=month, year=year)
            return {'revenue': ledger.revenue, 'profit': ledger.net_profit, 'advance_received': ledger.advance_received, 'gross_profit': ledger.gross_profit, 'net_profit': ledger.net_profit}
        except Ledger.DoesNotExist:
            return {'revenue': 0, 'profit': 0}  # Or provide default values

    def get(self, request):

        current_month = datetime.now().month
        current_year = datetime.now().year

        last_12_months = [
            (
                self.get_month_name((current_month - x - 1) % 12 + 1),
                (current_month - x - 1) % 12 + 1,
                current_year if (current_month - x) > 0 else current_year - 1
            )
            for x in range(12)
        ]

        financial_data_list = [self.get_financial_data(
            month=i[1], year=i[2]) for i in last_12_months]

        revenue_list = [data['revenue']
                        for data in financial_data_list]
        total_revenue = sum(revenue_list)

        growth_rates = [(revenue_list[i] - revenue_list[i - 1]) /
                        revenue_list[i - 1] * 100 for i in range(1, len(revenue_list))]

        # Calculate the average growth rate
        average_growth_rate = sum(growth_rates) / len(growth_rates)

        pct_net_profit = (sum([data['net_profit']
                              for data in financial_data_list])/total_revenue) * 100

        pct_gross_profit = (sum([data['gross_profit']
                                for data in financial_data_list])/total_revenue) * 100

        pct_ac_receivables = (sum([data['advance_received']
                                  for data in financial_data_list])/total_revenue) * 100
        response_data = {
            'last_12_months': [i[0] for i in last_12_months][::-1],
            'revenue_list': revenue_list[::-1],
            'profit_list': [data['profit'] for data in financial_data_list][::-1],
            'total_revenue': total_revenue,
            'average_growth_rate': average_growth_rate,
            'advance_list': [data['advance_received'] for data in financial_data_list][::-1],
            'cash_in_hand': Cash.objects.first().cash,
            'pct_net_profit': pct_net_profit,
            'pct_gross_profit': pct_gross_profit,
            'pct_ac_receivables': pct_ac_receivables,
        }

        return Response(response_data)


class CurrentMonthTotals(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Ledger.objects.all()

    def get(self, request):
        today = datetime.now()

        # Calculate the start of the current month
        current_month_start = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate the start of the next month using relativedelta
        next_month_start = current_month_start + relativedelta(months=1)

        previous_month_start = current_month_start - relativedelta(months=1)

        current_total_clients_added = Client.objects.filter(
            date_added__gte=current_month_start, date_added__lt=next_month_start).count()

        previous_total_clients_added = Client.objects.filter(
            date_added__gte=previous_month_start, date_added__lt=current_month_start).count()

        client_growth = ((current_total_clients_added -
                         previous_total_clients_added) / previous_total_clients_added) * 100

        current_total_events = Event.objects.filter(
            date__gte=current_month_start, date__lt=next_month_start).count()

        previous_total_events = Event.objects.filter(
            date__gte=previous_month_start, date__lt=current_month_start).count()

        event_growth = (
            (current_total_events - previous_total_events) / previous_total_events) * 100

        current_total_revenue = self.queryset.get(
            month=current_month_start.month, year=current_month_start.year).revenue

        previous_total_revenue = self.queryset.get(
            month=previous_month_start.month, year=previous_month_start.year).revenue
        revenue_growth = (
            (current_total_revenue - previous_total_revenue) / previous_total_revenue) * 100

        response_data = {
            "customers": current_total_clients_added,
            "customers_growth": client_growth,
            "events": current_total_events,
            "events_growth": event_growth,
            "revenue": current_total_revenue,
            "revenue_growth": revenue_growth
        }

        return Response(response_data)


class PackageWiseRevenue(APIView):
    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.SessionAuthentication]
    queryset = Package.objects.all()

    def get(self, request):
        response_data = []
        for package in self.queryset.filter(active=True):
            name = package.name
            budget = package.budget
            qty_sold = package.get_qty_sold()

            expected_revenue = budget*qty_sold

            total_revenue = sum([
                event.get_total_budget() for event in Event.objects.filter(package=package)
            ])

            data = {
                "name": name,
                "budget": budget,
                "qty_sold": qty_sold,
                "expected_revenue": expected_revenue,
                "total_revenue": total_revenue,
            }

            response_data.append(data)

        return Response(response_data)
