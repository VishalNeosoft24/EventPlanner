from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from events.utils import upload_image_to_s3, delete_image_from_s3
from .forms import RegisterForm, EventForm
from .models import Event, RSVP
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings

def home(request):
    events_list = Event.objects.order_by('date')
    paginator = Paginator(events_list, 5)  # Show 5 events per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'events/home.html', {'page_obj': page_obj})


def event_detail(request, event_id):
    # Fetch the event with the given event_id or return a 404 error if not found
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
            # Log the user in automatically after registration
            login(request, user)
            messages.success(request, 'Welcome! You have successfully registered!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'events/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
    else:
        form = AuthenticationForm()

    # Add Bootstrap class dynamically(boostrap5)
    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'form-control',
        })

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, 'You have successfully logged in!')
        return redirect('home')

    return render(request, 'events/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have successfully logged out!')
    return redirect('home')


# Event Create (Authenticated User)
@login_required(login_url='/login/')
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user

            image_file = request.FILES.get('image')
            if image_file:
                s3_url = upload_image_to_s3(image_file)
                event.image = s3_url

            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('home')
    else:
        form = EventForm()
    return render(request, 'events/create_event.html', {
        'form': form,
        'is_update': False
    })


# Event Update (Authenticated User)
@login_required(login_url='/login/')
def update_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save(commit=False)

            image_file = request.FILES.get('image')
            if image_file:
                # Upload new image and update the S3 URL
                s3_url = upload_image_to_s3(image_file)
                event.image = s3_url  # This overwrites old image URL

            event.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)

    return render(request, 'events/create_event.html', {
        'form': form,
        'is_update': True,
        'event': event
    })


# Event Delete (Authenticated User)
@login_required(login_url='/login/')
def delete_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)

    if request.method == 'POST':
        # Delete image from S3 if it exists
        if event.image:
            delete_image_from_s3(str(event.image))

        # Delete the event from DB
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('home')

    return render(request, 'events/confirm_delete.html', {'event': event})

# RSVP to Event
@login_required(login_url='/login/')
def toggle_rsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    rsvp, created = RSVP.objects.get_or_create(user=request.user, event=event)

    if not created:
        # Already exists -> user wants to un-RSVP
        rsvp.delete()
    # If created, RSVP was added successfully

    return redirect('event_detail', event_id=event.id)