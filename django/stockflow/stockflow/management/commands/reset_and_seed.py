from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Reset database and seed all initial data'

    def handle(self, *args, **kwargs):
        db_file = 'db.sqlite3'
        if os.path.exists(db_file):
            os.remove(db_file)
            self.stdout.write(self.style.WARNING(f"Deleted {db_file}"))

        self.stdout.write(self.style.NOTICE("Running migrations..."))
        call_command('migrate')

        self.stdout.write(self.style.NOTICE("Seeding users..."))
        call_command('seed_users', '--clean')

        self.stdout.write(self.style.NOTICE("Seeding category..."))
        call_command('seed_category')

        self.stdout.write(self.style.NOTICE("Seeding items..."))
        call_command('seed_item')
        
        self.stdout.write(self.style.NOTICE("Seeding BOMs..."))
        call_command('seed_bom')
        
        self.stdout.write(self.style.NOTICE("Seeding warehouses..."))
        call_command('seed_warehouse')
        
        self.stdout.write(self.style.NOTICE("Seeding stock movements..."))
        call_command('seed_stock_movement')
        
        self.stdout.write(self.style.NOTICE("Seeding stock movement items..."))
        call_command('seed_item_movement')

        self.stdout.write(self.style.SUCCESS("✅ Reset and seed completed!"))
