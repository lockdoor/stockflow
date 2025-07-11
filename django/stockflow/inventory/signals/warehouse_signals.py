from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from inventory.models.warehouse import Warehouse
from django.contrib.contenttypes.models import ContentType

@receiver(post_save, sender=Warehouse)
def create_warehouse_group_and_permission(sender, instance, created, **kwargs):
    if created:
        # สร้าง group สำหรับ warehouse นี้
        group_name = f"warehouse_{instance.id}_staff"
        group, _ = Group.objects.get_or_create(name=group_name)

        # สร้าง permission เฉพาะ warehouse (ตัวอย่าง: view/manage)
        content_type = ContentType.objects.get_for_model(Warehouse)
        perm_codename = f"can_manage_warehouse_{instance.id}"
        perm_name = f"Can manage Warehouse {instance.name} (ID {instance.id})"
        permission, _ = Permission.objects.get_or_create(
            codename=perm_codename,
            name=perm_name,
            content_type=content_type
        )
        # เพิ่ม permission ให้ group
        group.permissions.add(permission)

        # เพิ่ม permission ให้ group superuser ด้วย
        superuser_group, _ = Group.objects.get_or_create(name='superuser')
        superuser_group.permissions.add(permission)
