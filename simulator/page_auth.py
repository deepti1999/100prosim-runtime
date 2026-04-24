"""Authentication and top-level page views."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render

from .models import LandUse, RenewableData

def landing_page(request):
    """Landing page for 100ProSim application"""
    return render(request, 'simulator/landing_page.html')

def user_guide(request):
    """Static quick-start guide with visual pointers to key pages"""
    return render(request, 'simulator/guide.html')

def test_storage(request):
    """Test page for localStorage debugging"""
    return render(request, 'simulator/test_storage.html')

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Willkommen zurück, {username}!')
                return redirect('simulator:main_simulation')
            else:
                messages.error(request, 'Ungültiger Benutzername oder Passwort.')
        else:
            messages.error(request, 'Ungültiger Benutzername oder Passwort.')
    else:
        form = AuthenticationForm()
    return render(request, 'simulator/login.html', {'form': form})

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Konto für {username} erstellt! Sie können sich jetzt anmelden.')
            return redirect('simulator:login')
        else:
            messages.error(request, 'Bitte korrigieren Sie die Fehler unten.')
    else:
        form = UserCreationForm()
    return render(request, 'simulator/register.html', {'form': form})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'Sie wurden erfolgreich abgemeldet.')
    return redirect('simulator:landing_page')

@login_required
def main_simulation(request):
    """Main simulation dashboard with sidebar navigation"""
    context = {
        'current_section': 'dashboard',
        'total_landuse_records': LandUse.objects.count(),
        'total_renewable_records': RenewableData.objects.count(),
    }
    return render(request, 'simulator/main_simulation.html', context)

@login_required
def user_manual(request):
    """User manual page with step-by-step guide and screenshots"""
    context = {
        'current_section': 'user_manual',
    }
    return render(request, 'simulator/user_manual.html', context)
