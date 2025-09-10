"""
Management command to create warehouse permissions for existing warehouses
"""

from django.core.management.base import BaseCommand
from inventory.models import Warehouse


class Command(BaseCommand):
    help = 'Create warehouse-specific permissions for existing warehouses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--warehouse-id',
            type=int,
            help='Create permissions for specific warehouse ID only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate permissions even if they exist',
        )

    def handle(self, *args, **options):
        warehouse_id = options.get('warehouse_id')
        force = options.get('force', False)

        if warehouse_id:
            warehouses = Warehouse.objects.filter(id=warehouse_id)
            if not warehouses.exists():
                self.stdout.write(
                    self.style.ERROR(f'Warehouse with ID {warehouse_id} does not exist')
                )
                return
        else:
            warehouses = Warehouse.objects.all()

        created_count = 0
        updated_count = 0

        for warehouse in warehouses:
            self.stdout.write(f'Processing warehouse: {warehouse}')
            
            # Check if permissions already exist
            group_name = f"warehouse_{warehouse.id}_staff"
            from django.contrib.auth.models import Group
            
            try:
                group = Group.objects.get(name=group_name)
                if force:
                    # Delete existing permissions and recreate
                    from django.contrib.auth.models import Permission
                    warehouse_permissions = Permission.objects.filter(
                        codename__endswith=f"_warehouse_{warehouse.id}"
                    )
                    count = warehouse_permissions.count()
                    warehouse_permissions.delete()
                    group.delete()
                    
                    self.stdout.write(
                        self.style.WARNING(f'Deleted {count} existing permissions for {warehouse}')
                    )
                    
                    # Recreate
                    group, permissions = warehouse._create_warehouse_permissions()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Recreated {len(permissions)} permissions for {warehouse}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Permissions already exist for {warehouse}. Use --force to recreate.')
                    )
                    
            except Group.DoesNotExist:
                # Create new permissions
                group, permissions = warehouse._create_warehouse_permissions()
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created {len(permissions)} permissions for {warehouse}')
                )

        if warehouse_id:
            summary = f'Processed warehouse ID {warehouse_id}'
        else:
            summary = f'Processed {warehouses.count()} warehouses'
            
        self.stdout.write(
            self.style.SUCCESS(
                f'{summary}: {created_count} created, {updated_count} updated'
            )
        )
