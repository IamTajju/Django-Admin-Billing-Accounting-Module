from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path("view-bill/<int:bill_id>", views.view_bill,
         name="view-bill"),
    path("new-bill/<int:client_id>/",
         views.generate_new_bill, name="generate_new_bill")
]
