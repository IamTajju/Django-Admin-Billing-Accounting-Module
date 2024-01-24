from django.urls import path, include
from . import views
from rest_framework import routers

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'clients', views.ClientViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'add-ons', views.AddOnViewSet)
router.register(r'cashinflows', views.CashInflowViewSet)
router.register(r'cashoutflows', views.CashOutflowViewSet)
router.register(r'teammemberbills', views.TeamMemberBillViewSet)
router.register(r'teammembers', views.TeamMemberViewSet)
router.register(r'packages', views.PackageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('setcsrf', views.setCSRFCookie.as_view()),
    path('user-login', views.LoginView.as_view()),
    path('user-logout', views.LogoutView.as_view()),
    path('client-tableview', views.ClientTableView.as_view()),
    path('event-tableview', views.EventTableView.as_view()),
    path('cashinflow-tableview', views.CashInflowTableView.as_view()),
    path('bill-tableview', views.HistoricalBillTableView.as_view()),
    path('package-tableview', views.PackageTableView.as_view()),
    path('ledger-tableview', views.LedgerTableView.as_view()),
    path('client-pending-payment', views.ClientPendingPayment.as_view()),
    path('cea-registration', views.CEARegistration.as_view()),
    path('last-year-financial-summary', views.LastYearFinancialSummary.as_view()),
    path('current-month-totals', views.CurrentMonthTotals.as_view()),
    path('package-wise-revenue', views.PackageWiseRevenue.as_view()),
]
