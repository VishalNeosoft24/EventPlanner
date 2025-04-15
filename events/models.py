from django.db import models
from django.contrib.auth.models import User
import uuid

def event_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"banner_{uuid.uuid4()}.{ext}"
    return f'events/{instance.id or "new"}/{filename}'


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to=event_image_upload_path, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class RSVP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')  # Prevent duplicate RSVPs

    def __str__(self):
        return f"{self.user.username} RSVP'd to {self.event.title}"
