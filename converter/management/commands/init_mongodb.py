from django.core.management.base import BaseCommand
from converter.mongo_config import connect_mongodb, init_mongodb_collections, check_mongodb_health
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize MongoDB connection and collections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check MongoDB connection without initializing collections',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting MongoDB initialization...'))
        
        try:
            # Check MongoDB connection
            if not check_mongodb_health():
                self.stdout.write(self.style.ERROR('MongoDB connection failed'))
                return
            
            self.stdout.write(self.style.SUCCESS('MongoDB connection successful'))
            
            if options['check_only']:
                self.stdout.write(self.style.SUCCESS('MongoDB health check completed'))
                return
            
            # Initialize MongoEngine connection
            if connect_mongodb():
                self.stdout.write(self.style.SUCCESS('MongoEngine connection established'))
            else:
                self.stdout.write(self.style.ERROR('MongoEngine connection failed'))
                return
            
            # Initialize collections and indexes
            if init_mongodb_collections():
                self.stdout.write(self.style.SUCCESS('MongoDB collections and indexes initialized'))
            else:
                self.stdout.write(self.style.ERROR('Failed to initialize MongoDB collections'))
                return
            
            self.stdout.write(self.style.SUCCESS('MongoDB initialization completed successfully'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'MongoDB initialization failed: {e}'))
            logger.error(f'MongoDB initialization error: {e}')
