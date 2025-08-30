# Zoom Login Page - Django Project

A beautiful Zoom-like login page built with Django.

## Features

- Modern, responsive design
- User authentication (login/logout)
- Beautiful UI with Zoom-inspired styling
- Django messages for user feedback
- Ready for production deployment

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Deployment on Render

### Prerequisites
- A Render account
- Git repository with your code

### Steps

1. **Create a new Web Service on Render**
   - Connect your Git repository
   - Choose "Python" as the environment

2. **Configure the service:**
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn registration_project.wsgi:application`
   - **Environment:** Python 3.9 or higher

3. **Set Environment Variables:**
   - `SECRET_KEY`: Generate a secure secret key
   - `DEBUG`: Set to `False` for production
   - `DATABASE_URL`: Will be automatically set by Render

4. **Database Setup:**
   - Create a PostgreSQL database on Render
   - The `DATABASE_URL` will be automatically configured

### Environment Variables

Set these in your Render dashboard:

```
SECRET_KEY=your-secure-secret-key-here
DEBUG=False
```

### Build Script

The `build.sh` script will:
- Install dependencies
- Collect static files
- Run database migrations

## Project Structure

```
├── accounts/
│   ├── templates/
│   │   └── home.html          # Main login/home page
│   ├── views.py               # View logic
│   └── urls.py                # URL routing
├── registration_project/
│   ├── settings.py            # Django settings
│   └── urls.py                # Main URL configuration
├── requirements.txt           # Python dependencies
├── build.sh                   # Render build script
└── manage.py                  # Django management script
```

## Customization

- Modify `accounts/templates/home.html` to change the design
- Update `accounts/views.py` to add new functionality
- Add new apps in `registration_project/settings.py`

## Security Notes

- The project includes production security settings
- CSRF protection is enabled
- HTTPS redirects are configured for production
- Static files are served securely with WhiteNoise

## Support

For deployment issues, check:
- Render logs in the dashboard
- Django debug settings
- Database connection configuration 
