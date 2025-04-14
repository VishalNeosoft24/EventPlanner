from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, EventForm
from .models import Event, RSVP
from django.contrib import messages

def home(request):
    events = Event.objects.order_by('date')
    return render(request, 'events/home.html', {'events': events})

def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    has_rsvped = False
    if request.user.is_authenticated:
        has_rsvped = RSVP.objects.filter(user=request.user, event=event).exists()
    return render(request, 'events/event_detail.html', {
        'event': event,
        'has_rsvped': has_rsvped,
    })


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'events/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'events/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')


# Event Create (Authenticated User)
@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('home')
    else:
        form = EventForm()
    return render(request, 'events/create_event.html', {'form': form})

# Event Update (Authenticated User)
@login_required
def update_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    return render(request, 'events/create_event.html', {'form': form})

# Event Delete (Authenticated User)
@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('home')
    return render(request, 'events/confirm_delete.html', {'event': event})

# RSVP to Event
@login_required
def toggle_rsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    rsvp, created = RSVP.objects.get_or_create(user=request.user, event=event)

    if not created:
        # Already exists -> user wants to un-RSVP
        rsvp.delete()
    # If created, RSVP was added successfully

    return redirect('event_detail', event_id=event.id)
