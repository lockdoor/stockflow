"""
Stock Movement Validators

Validators for StockMovement model to ensure data integrity and business rules.

Author: StockFlow Team
Created: 2025
"""

from django.core.exceptions import ValidationError
from django.db import models


def validate_reference_consistency(instance):
    """
    Validate that reference_id is provided when reference_type is not NONE
    """
    if (instance.reference_type != 'NONE' and 
        instance.reference_type != '' and 
        not instance.reference_id):
        raise ValidationError({
            'reference_id': 'Reference ID is required when reference type is specified.'
        })


def validate_warehouse_active(instance):
    """
    Validate that the warehouse is active when creating/updating stock movement
    """
    if instance.warehouse and not instance.warehouse.is_active:
        raise ValidationError({
            'warehouse': 'Cannot create stock movement for inactive warehouse.'
        })


def validate_status_transition(instance):
    """
    Validate that status transitions are allowed
    """
    if instance.pk:
        try:
            current = instance.__class__.objects.get(pk=instance.pk)
            if current.status == 'CONFIRMED' and instance.status != 'CONFIRMED':
                raise ValidationError({
                    'status': 'Cannot change status from CONFIRMED to other status.'
                })
        except instance.__class__.DoesNotExist:
            # New instance, no validation needed
            pass


def validate_unique_draft_per_warehouse(instance):
    """
    Validate that there is only one DRAFT stock movement per warehouse
    """
    if instance.status == 'DRAFT':
        existing_drafts = instance.__class__.objects.filter(
            warehouse=instance.warehouse,
            status='DRAFT'
        )
        
        if instance.pk:
            existing_drafts = existing_drafts.exclude(pk=instance.pk)
        
        if existing_drafts.exists():
            raise ValidationError({
                'warehouse': f'Warehouse {instance.warehouse.name} already has a draft stock movement.'
            })


def validate_confirmed_immutability(instance):
    """
    Validate that confirmed stock movements cannot be modified (except for version)
    """
    if instance.pk:
        try:
            current = instance.__class__.objects.get(pk=instance.pk)
            if current.status == 'CONFIRMED':
                # Check if any field other than version has changed
                excluded_fields = ['version', 'updated_at', 'updated_by']
                for field in instance._meta.fields:
                    if field.name not in excluded_fields:
                        current_value = getattr(current, field.name)
                        new_value = getattr(instance, field.name)
                        if current_value != new_value:
                            raise ValidationError(
                                'Confirmed stock movements cannot be modified.'
                            )
        except instance.__class__.DoesNotExist:
            # New instance, no validation needed
            pass
