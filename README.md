# EventPlanner

**EventPlanner** is an event management web application built with Django. The project allows users to create, update, and delete events as well as RSVP (and cancel RSVPs) for events. It supports user authentication and restricts editing and deletion of events to the respective creators. This initial release (MVP) lays a foundation that you can later extend with advanced features and integration with other services.

## Features

### User Authentication:
- User registration, login, and logout

### Event Management:
- Create, view, update, and delete events
- Upload event banners/images

### RSVP Functionality:
- Users can RSVP to an event and cancel their RSVP

### Public Views:
- List upcoming events
- Detailed event view with RSVP status

### Access Control:
- Only event creators can edit or delete their events

## Future Scope

- Integration with external calendar services (e.g., Google Calendar)
- Enhanced RSVP management (guest count, status, etc.)
- REST API support using Django REST Framework
- Frontend modernization with React
- Deployment enhancements (Docker, Gunicorn, Nginx, AWS, etc.)
- Additional features like comments, event categories, ticketing, and more

## Tech Stack

- **Backend:** Django, Python  
- **Frontend:** Django Templates, Bootstrap 5  
- **Database:** SQLite for development (upgradeable to PostgreSQL)  
- **Media Storage:** Local filesystem (with potential migration to AWS S3)  
- **Version Control:** Git, GitHub

## Installation
