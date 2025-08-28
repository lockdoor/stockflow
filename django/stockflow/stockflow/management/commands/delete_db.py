from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = "Reset the database"
    
    def handle(self, *args, **kwargs):
        db_file = 'db.sqlite3'
        if os.path.exists(db_file):
            os.remove(db_file)
            self.stdout.write(self.style.WARNING(f"Deleted {db_file}"))