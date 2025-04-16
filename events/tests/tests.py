from datetime import datetime, timedelta
import io
from unittest.mock import patch
from PIL import Image

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, RSVP


class RegisterViewTest(TestCase):

    def test_register_get_request_renders_form(self):
        response = self.client.get(reverse('register'))  # assuming 'register' is the URL name
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/register.html')
        self.assertContains(response, '<form')

    def test_register_post_valid_data_creates_user_and_redirects(self):
        data = {

            'username': 'testuser',
            'email':'testemail@gmail.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
        }
        response = self.client.post(reverse('register'), data)
        
        # Check user is created
        self.assertTrue(User.objects.filter(username='testuser').exists())

        # Check user is authenticated (logged in)
        user = User.objects.get(username='testuser')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        # Check redirection to 'home'
        self.assertRedirects(response, reverse('home'))

    def test_register_post_invalid_data_renders_form_with_errors(self):
        data = {
            'username': 'testuser',
            'email':'testemail@gmail.com',
            'password1': 'pass',
            'password2': 'differentpass',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/register.html')
        self.assertFormError(response, 'form', 'password2', "The two password fields didn’t match.")


class LoginViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_login_get_renders_form(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/login.html')
        self.assertContains(response, '<form')

    def test_login_valid_credentials_redirects(self):
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('login'), data)
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_invalid_credentials_shows_error(self):
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/login.html')
        self.assertContains(response, 'Please enter a correct username and password')


class LogoutViewTest(TestCase):

    def setUp(self):
        # Create a user for testing the logout functionality
        self.user = get_user_model().objects.create_user(
            username='testuser', password='testpassword123'
        )
        self.url = reverse('logout')  # assuming 'logout' is the URL name for the logout view

    def test_logout_redirects_to_home(self):
        # Log in the user before testing logout
        self.client.login(username='testuser', password='testpassword123')
        
        # Make a GET request to the logout view
        response = self.client.get(self.url)
        
        # Check that the response redirects to the home page
        self.assertRedirects(response, reverse('home'))
        
        # Ensure the user is logged out (there should be no authenticated user)
        response = self.client.get(reverse('home'))
        
        # Check that the response doesn't have an authenticated user
        self.assertNotContains(response, 'testuser')  # Ensure 'testuser' is not in the response (logged-out)

    def test_logout_shows_success_message(self):
        # Log in the user before testing logout
        self.client.login(username='testuser', password='testpassword123')
        
        # Make a GET request to the logout view
        response = self.client.get(self.url)
        
        # Check that a success message is shown after logging out
        messages = list(response.wsgi_request._messages)
        print('messages: ', messages)
        self.assertEqual(str(messages[0]), 'You have successfully logged out!')

    def test_logout_without_login_redirects_to_home(self):
        # Ensure that if the user is not logged in, they are redirected to the home page
        response = self.client.get(self.url)
        
        # Check that the response redirects to the home page
        self.assertRedirects(response, reverse('home'))

        # Ensure no user is logged in (no session data for an authenticated user)
        user = self.client.session.get('_auth_user_id', None)
        self.assertIsNone(user)



class HomeViewTest(TestCase):

    def setUp(self):
        # Create a user for the 'created_by' field
        user = User.objects.create_user(username='testuser', password='password123')

        # Create sample events for testing with the 'created_by' user
        Event.objects.create(title='Event 1', date='2025-04-01', description='Description of event 1', created_by=user)
        Event.objects.create(title='Event 2', date='2025-04-02', description='Description of event 2', created_by=user)
        Event.objects.create(title='Event 3', date='2025-04-03', description='Description of event 3', created_by=user)
        Event.objects.create(title='Event 4', date='2025-04-04', description='Description of event 4', created_by=user)
        Event.objects.create(title='Event 5', date='2025-04-05', description='Description of event 5', created_by=user)
        Event.objects.create(title='Event 6', date='2025-04-06', description='Description of event 6', created_by=user)

    def test_home_view_with_pagination(self):
        # Test the home view with pagination (5 events per page)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/home.html')
        
        # Ensure that only 5 events are displayed on the first page
        self.assertContains(response, 'Event 1')
        self.assertContains(response, 'Event 2')
        self.assertContains(response, 'Event 3')
        self.assertContains(response, 'Event 4')
        self.assertContains(response, 'Event 5')
        self.assertNotContains(response, 'Event 6')

    def test_home_view_second_page(self):
        # Test pagination on the second page
        response = self.client.get(reverse('home') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/home.html')

        # Ensure that the second page contains the 6th event
        self.assertContains(response, 'Event 6')
        self.assertNotContains(response, 'Event 1')

    def test_home_view_no_events(self):
        # Test the case when no events exist
        Event.objects.all().delete()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No upcoming events found.')


class EventDetailViewTest(TestCase):

    def setUp(self):
        # Create a user for authentication
        self.user = User.objects.create_user(username='testuser', password='password123')

        # Create an event
        self.event = Event.objects.create(
            title='Test Event',
            date=timezone.make_aware(datetime(2025, 4, 2)),
            description='Description of the test event',
            created_by=self.user
        )

        # Create an RSVP for the user and event
        self.rsvp = RSVP.objects.create(
            user=self.user,
            event=self.event
        )

    def test_event_detail_view(self):
        # Test that the event detail page loads successfully
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_detail.html')
        self.assertContains(response, 'Test Event')  # Check the event title
        self.assertContains(response, 'Description of the test event')  # Check the event description

    def test_event_detail_with_rsvp(self):
        # Test that the 'has_rsvped' context variable is True when the user has RSVPed
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_rsvped'])  # Check RSVP status is True

    def test_event_detail_without_rsvp(self):
        # Test that the 'has_rsvped' context variable is False when the user has not RSVPed
        other_user = User.objects.create_user(username='otheruser', password='password123')
        self.client.login(username='otheruser', password='password123')
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['has_rsvped'])  # Check RSVP status is False

    def test_event_detail_user_not_authenticated(self):
        # Test that the 'has_rsvped' context variable is False when the user is not authenticated
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['has_rsvped'])  # Check RSVP status is False


class CreateEventViewTestCase(TestCase):
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # URL for the create event page
        self.url = reverse('create_event')

    def generate_test_image_file(self):
        image = Image.new('RGB', (100, 100), color='red')
        byte_io = io.BytesIO()
        image.save(byte_io, 'JPEG')
        byte_io.seek(0)
        return SimpleUploadedFile('test_image.jpg', byte_io.read(), content_type='image/jpeg')


    def test_create_event_successfully(self):
        self.client.login(username='testuser', password='testpassword')

        image_file = self.generate_test_image_file()

        event_data = {
            'title': 'Test Event',
            'description': 'Test event description',
            'location': 'Test location',
            'date': '2025-05-01 10:30',
            'image': image_file
        }

        with patch('events.views.upload_image_to_s3') as mock_upload_image_to_s3:
            mock_upload_image_to_s3.return_value = 'https://s3.amazonaws.com/fake-bucket/test_image.jpg'
            response = self.client.post(self.url, event_data)

            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('home'))

            event = Event.objects.last()
            self.assertEqual(event.title, 'Test Event')
            self.assertEqual(event.description, 'Test event description')
            self.assertEqual(event.created_by, self.user)
            self.assertEqual(event.image, 'https://s3.amazonaws.com/fake-bucket/test_image.jpg')


    def test_create_event_invalid_form(self):
        # Log the user in
        self.client.login(username='testuser', password='testpassword')

        # Prepare invalid event form data (missing required fields)
        event_data = {
            'title': '',  # Invalid title
            'description': 'Test event description',
            'location': 'Test location',
            'date': '2025-05-01 10:30',
        }

        # Make a POST request to create an event
        response = self.client.post(self.url, event_data)

        # Check that the form is not valid and re-renders the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'title', 'This field is required.')

    def test_create_event_not_logged_in(self):
        # Simulate a request without logging in
        response = self.client.get(self.url)
        
        # Update the redirect URL to reflect your actual login URL
        self.assertRedirects(response, f'/login/?next={self.url}')




class UpdateEventViewTestCase(TestCase):
    def setUp(self):
        # Create a test user and log in
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create an event
        self.event = Event.objects.create(
            title='Original Title',
            description='Original Description',
            location='Original Location',
            date='2025-05-01 10:30',
            created_by=self.user,
            image='https://s3.amazonaws.com/fake-bucket/original.jpg'
        )

        self.url = reverse('update_event', args=[self.event.id])

    def generate_test_image_file(self):
        image = Image.new('RGB', (100, 100), color='blue')
        byte_io = io.BytesIO()
        image.save(byte_io, 'JPEG')
        byte_io.seek(0)
        return SimpleUploadedFile('test_image.jpg', byte_io.read(), content_type='image/jpeg')

    def test_update_event_successfully(self):
        updated_image = self.generate_test_image_file()

        updated_data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'location': 'Updated Location',
            'date': '2025-05-02 15:00',
            'image': updated_image
        }

        with patch('events.views.upload_image_to_s3') as mock_upload_image_to_s3:
            mock_upload_image_to_s3.return_value = 'https://s3.amazonaws.com/fake-bucket/updated.jpg'

            response = self.client.post(self.url, updated_data)

            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('event_detail', args=[self.event.id]))

            # Refresh from DB
            self.event.refresh_from_db()

            self.assertEqual(self.event.title, 'Updated Title')
            self.assertEqual(self.event.description, 'Updated Description')
            self.assertEqual(self.event.location, 'Updated Location')
            self.assertEqual(self.event.date.strftime('%Y-%m-%d %H:%M'), '2025-05-02 15:00')
            self.assertEqual(self.event.image, 'https://s3.amazonaws.com/fake-bucket/updated.jpg')


    def test_update_event_unauthorized(self):
        # Log out current user
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')


from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from events.models import Event
from unittest.mock import patch

class DeleteEventViewTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create an event for deletion
        self.event = Event.objects.create(
            title='Delete Me',
            description='To be deleted',
            location='Nowhere',
            date='2025-05-01 10:00',
            created_by=self.user,
            image='https://s3.amazonaws.com/fake-bucket/delete_me.jpg'
        )

        self.url = reverse('delete_event', args=[self.event.id])

    def test_delete_event_successfully(self):
        # Mock S3 deletion
        with patch('events.views.delete_image_from_s3') as mock_delete_image:
            response = self.client.post(self.url)

            # Check redirection
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('home'))

            # Event should be deleted
            self.assertFalse(Event.objects.filter(id=self.event.id).exists())

            # Ensure the S3 image deletion function was called
            mock_delete_image.assert_called_once_with(str(self.event.image))

    def test_delete_event_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_delete_event_confirmation_page(self):
        # Access confirmation page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/confirm_delete.html')
        self.assertContains(response, 'Delete Me')




class ToggleRSVPViewTestCase(TestCase):
    def setUp(self):
        # Create a user and log in
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create a test event
        self.event = Event.objects.create(
            title='RSVP Event',
            description='RSVP test event',
            location='Test Venue',
            date=datetime.now() + timedelta(days=1),
            created_by=self.user
        )

        self.url = reverse('toggle_rsvp', args=[self.event.id])

    def test_rsvp_created_successfully(self):
        # Ensure RSVP does not exist initially
        self.assertFalse(RSVP.objects.filter(user=self.user, event=self.event).exists())

        response = self.client.post(self.url)

        # After POST, RSVP should be created
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event_detail', args=[self.event.id]))
        self.assertTrue(RSVP.objects.filter(user=self.user, event=self.event).exists())

    def test_rsvp_removed_successfully(self):
        # Create RSVP manually
        RSVP.objects.create(user=self.user, event=self.event)
        self.assertTrue(RSVP.objects.filter(user=self.user, event=self.event).exists())

        # Post to remove RSVP
        response = self.client.post(self.url)

        # RSVP should be removed
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event_detail', args=[self.event.id]))
        self.assertFalse(RSVP.objects.filter(user=self.user, event=self.event).exists())

    def test_toggle_rsvp_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')
