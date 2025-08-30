from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        """Initialize MongoDB connection when Django starts"""
        try:
            from registration_project.mongodb import connect_to_mongodb
            connect_to_mongodb()
        except Exception as e:
            print(f"Warning: Could not connect to MongoDB: {e}")
