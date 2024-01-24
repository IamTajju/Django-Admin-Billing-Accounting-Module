from django.shortcuts import redirect


def redirect_to_root(request):
    return redirect('/')
