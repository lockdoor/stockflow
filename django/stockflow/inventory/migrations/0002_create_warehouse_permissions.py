"""
Data migration to create warehouse permissions for existing warehouses
"""

from django.db import migrations


def create_warehouse_permissions(apps, schema_editor):
    """Create permissions for existing warehouses"""
    Warehouse = apps.get_model('inventory', 'Warehouse')
    
    for warehouse in Warehouse.objects.all():
        # Use the actual method from the model
        try:
            warehouse._create_warehouse_permissions()
            print(f"Created permissions for warehouse: {warehouse}")
        except Exception as e:
            print(f"Failed to create permissions for warehouse {warehouse}: {e}")


def reverse_warehouse_permissions(apps, schema_editor):
    """Remove warehouse permissions (reverse migration)"""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    
    # Remove all warehouse-specific groups and permissions
    warehouse_groups = Group.objects.filter(name__startswith='warehouse_')
    warehouse_groups.delete()
    
    warehouse_permissions = Permission.objects.filter(
        codename__contains='_warehouse_'
    )
    warehouse_permissions.delete()
    
    print("Removed all warehouse-specific permissions and groups")


class Migration(migrations.Migration):
    
    dependencies = [
        ('inventory', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    
    operations = [
        migrations.RunPython(
            create_warehouse_permissions,
            reverse_warehouse_permissions,
        ),
    ]
