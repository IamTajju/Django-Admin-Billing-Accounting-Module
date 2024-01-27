from django.http import HttpResponse
import logging
from .models import *
from django.template.loader import render_to_string
from django.shortcuts import render
from weasyprint import HTML, CSS
import tempfile


def generate_new_bill(request, client_id, from_admin=None):
    user = User.objects.get(id=request.user.id)
    client = Client.objects.get(id=client_id)
    if from_admin:
        return view_bill(request, client.generate_bill(user), from_admin)
    return view_bill(request, client.generate_bill(user))


def view_bill(request, bill_id, from_admin=None):
    if from_admin:
        return render(request, "billing/admin-billing-download-view.html", {'bill_id': bill_id})
   
    bill = Bill.objects.get(id=bill_id)
    # For Direct loading HTML view
    # return render(request, 'billing/bill-pdf.html', {'bill': bill})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + \
        "INV" + str(bill_id) + '.pdf'

    response['Content-Transfer-Encoding'] = 'binary'
    html_string = render_to_string(
        'billing/bill-pdf.html', {'bill': bill, 'user': str(bill.user)})

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    # CSS(settings.STATIC_ROOT + '/billing/css/bootstrap.min.css')
    result = html.write_pdf(presentational_hints=True, stylesheets=[CSS("https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css")])
    # result = html.write_pdf(presentational_hints=True, stylesheets=[
    #                         CSS(settings.STATIC_ROOT + '/billing/css/bootstrap.min.css')])

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output = open(output.name, 'rb')
        response.write(output.read())
    return response
