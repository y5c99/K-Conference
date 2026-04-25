from django.shortcuts import render

# Create your views here.
"""
Views for the 'accounts' app.
Handles signup (two steps), login, logout, and dashboard routing.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from .forms import SignUpDetailsForm, EmailLoginForm
from .models import Profile


# ----------------------------------------------------------------------
# SIGN UP — two steps
# ----------------------------------------------------------------------

# Valid roles the user can pick on Step 1.
VALID_ROLES = [r[0] for r in Profile.ROLE_CHOICES]


def signup_role(request):
    """
    Step 1: Role Selection.
    User picks Organiser / Author / Reviewer / Participant.
    The choice is stored in the session and we redirect to Step 2.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        role = request.POST.get('role')
        if role in VALID_ROLES:
            # Stash the chosen role in the session for Step 2.
            request.session['signup_role'] = role
            return redirect('accounts:signup_details')
        else:
            messages.error(request, 'Please select a role to continue.')

    # Pre-select whichever role was previously chosen (if any).
    selected = request.session.get('signup_role', '')

    context = {
        'roles': [
            {'value': 'organiser',   'name': 'Organiser',
             'description': 'I am managing this conference'},
            {'value': 'author',      'name': 'Author',
             'description': 'I want to submit a paper'},
            {'value': 'reviewer',    'name': 'Reviewer',
             'description': 'I want to review submissions'},
            {'value': 'participant', 'name': 'Participant',
             'description': 'I want to attend this conference'},
        ],
        'selected': selected,
    }
    return render(request, 'accounts/signup_role.html', context)


def signup_details(request):
    """
    Step 2: Account details.
    Reads the role from the session (set in Step 1), creates the User,
    saves the Profile, logs the user in, and sends them to their dashboard.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    # Make sure Step 1 was completed.
    role = request.session.get('signup_role')
    if role not in VALID_ROLES:
        messages.info(request, 'Please choose your role first.')
        return redirect('accounts:signup_role')

    if request.method == 'POST':
        form = SignUpDetailsForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Update the auto-created Profile with role + affiliation.
            profile = user.profile
            profile.role = role
            profile.affiliation = form.cleaned_data['affiliation']
            profile.save()

            # Clear the session role and log them in.
            request.session.pop('signup_role', None)
            login(request, user)

            messages.success(request, 'Welcome to K-Conference!')
            return redirect('accounts:dashboard')
    else:
        form = SignUpDetailsForm()

    return render(request, 'accounts/signup_details.html', {
        'form': form,
        'role': role,
    })


# ----------------------------------------------------------------------
# LOGIN / LOGOUT
# ----------------------------------------------------------------------

def login_view(request):
    """The 'Welcome Back' login screen."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:dashboard')
    else:
        form = EmailLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Log the user out and send them home."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


# ----------------------------------------------------------------------
# DASHBOARD ROUTING
# ----------------------------------------------------------------------

@login_required
def dashboard_redirect(request):
    """
    Smart router: sends each user to the dashboard for their role.
    """
    role = request.user.profile.role
    if role == Profile.ROLE_ORGANISER:
        return redirect('accounts:dashboard_organiser')
    if role == Profile.ROLE_AUTHOR:
        return redirect('accounts:dashboard_author')
    if role == Profile.ROLE_REVIEWER:
        return redirect('accounts:dashboard_reviewer')
    return redirect('accounts:dashboard_participant')


# Each dashboard is a placeholder for now. We'll fill them with real
# data in later phases.

@login_required
def dashboard_organiser(request):
    if not request.user.profile.is_organiser():
        messages.error(request, 'You do not have permission to view that page.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/dashboard_organiser.html')


@login_required
def dashboard_author(request):
    if not request.user.profile.is_author():
        messages.error(request, 'You do not have permission to view that page.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/dashboard_author.html')


@login_required
def dashboard_reviewer(request):
    if not request.user.profile.is_reviewer():
        messages.error(request, 'You do not have permission to view that page.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/dashboard_reviewer.html')


@login_required
def dashboard_participant(request):
    if not request.user.profile.is_participant():
        messages.error(request, 'You do not have permission to view that page.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/dashboard_participant.html')