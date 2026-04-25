"""
Views for the 'core' app.
A view takes a request and returns a response (usually an HTML page).
"""

from django.shortcuts import render


def home(request):
    """
    The public home page of K-Conference.
    Anyone can visit this — no login required.
    """
    return render(request, 'core/home.html')