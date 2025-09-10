"""
Management command to assign users to warehouses
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import Warehouse


class Command(BaseCommand):
    help = 'Assign users to warehouse groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='Username to assign',
        )
        parser.add_argument(
            '--warehouse',
            type=int,
            required=True,
            help='Warehouse ID to assign user to',
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove user from warehouse instead of adding',
        )

    def handle(self, *args, **options):
        username = options['user']
        warehouse_id = options['warehouse']
        remove = options['remove']

        # Get user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" does not exist')
            )
            return

        # Get warehouse
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Warehouse with ID {warehouse_id} does not exist')
            )
            return

        if remove:
            # Remove user from warehouse
            success = warehouse.remove_user(user)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully removed user "{username}" from warehouse "{warehouse}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to remove user "{username}" from warehouse "{warehouse}"'
                    )
                )
        else:
            # Assign user to warehouse
            success = warehouse.assign_user(user)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully assigned user "{username}" to warehouse "{warehouse}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to assign user "{username}" to warehouse "{warehouse}"'
                    )
                )

        # Show current assignments
        assigned_warehouses = Warehouse.get_user_warehouses(user)
        if assigned_warehouses.exists():
            warehouse_names = ', '.join([str(w) for w in assigned_warehouses])
            self.stdout.write(f'User "{username}" is now assigned to: {warehouse_names}')
        else:
            self.stdout.write(f'User "{username}" is not assigned to any warehouses')
