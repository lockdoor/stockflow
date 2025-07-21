"""
Test Warehouse Model

Tests for the refactored Warehouse model using mixins architecture.
Tests validation, audit fields, status management, and business logic.

Author: StockFlow Team
Created: 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from inventory.models.warehouse import Warehouse


class WarehouseModelTest(TestCase):
    """Test case for Warehouse model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_warehouse_creation_with_valid_data(self):
        """Test creating warehouse with valid data"""
        warehouse = Warehouse(
            name="Main Warehouse",
            code="MAIN01",
            address="123 Storage St",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should pass validation
        is_valid, errors = warehouse.is_valid()
        self.assertTrue(is_valid, f"Validation failed: {errors}")
        
        # Save should work
        warehouse.save()
        self.assertIsNotNone(warehouse.pk)
        self.assertEqual(warehouse.code, "MAIN01")

    def test_warehouse_name_validation(self):
        """Test warehouse name validation"""
        # Empty name
        warehouse = Warehouse(
            name="",
            code="TEST01",
            created_by=self.user,
            updated_by=self.user
        )
        is_valid, errors = warehouse.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("Name is required", str(errors))

        # Too short name
        warehouse.name = "A"
        is_valid, errors = warehouse.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("at least 2 characters", str(errors))

    def test_warehouse_code_validation(self):
        """Test warehouse code validation"""
        # Invalid code format
        warehouse = Warehouse(
            name="Test Warehouse",
            code="test@123",  # Invalid characters
            created_by=self.user,
            updated_by=self.user
        )
        is_valid, errors = warehouse.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("alphanumeric characters", str(errors))

    def test_warehouse_duplicate_prevention(self):
        """Test duplicate name and code prevention"""
        # Create first warehouse
        warehouse1 = Warehouse.objects.create(
            name="Warehouse One",
            code="WH001",
            created_by=self.user,
            updated_by=self.user
        )

        # Try to create with duplicate name
        warehouse2 = Warehouse(
            name="Warehouse One",  # Same name
            code="WH002",
            created_by=self.user,
            updated_by=self.user
        )
        is_valid, errors = warehouse2.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("already exists", str(errors))

        # Try to create with duplicate code
        warehouse3 = Warehouse(
            name="Warehouse Three",
            code="WH001",  # Same code
            created_by=self.user,
            updated_by=self.user
        )
        is_valid, errors = warehouse3.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("already exists", str(errors))

    def test_optimistic_locking(self):
        """Test optimistic locking functionality"""
        warehouse = Warehouse.objects.create(
            name="Lock Test Warehouse",
            code="LOCK01",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Get same warehouse in two different instances
        warehouse1 = Warehouse.objects.get(pk=warehouse.pk)
        warehouse2 = Warehouse.objects.get(pk=warehouse.pk)
        
        # Modify and save first instance
        warehouse1.name = "Modified Name 1"
        warehouse1.save()
        
        # Try to save second instance (should fail)
        warehouse2.name = "Modified Name 2"
        with self.assertRaises(ValidationError) as context:
            warehouse2.save()
        
        self.assertIn("modified by another user", str(context.exception))

    def test_status_management(self):
        """Test status management mixin"""
        warehouse = Warehouse.objects.create(
            name="Status Test Warehouse",
            code="STATUS01",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should be active by default
        self.assertTrue(warehouse.is_active)
        self.assertEqual(warehouse.status_display, "Active")
        
        # Test deactivation
        warehouse.deactivate()
        self.assertFalse(warehouse.is_active)
        self.assertEqual(warehouse.status_display, "Inactive")
        
        # Test toggle
        warehouse.toggle_status()
        self.assertTrue(warehouse.is_active)

    def test_audit_fields(self):
        """Test audit fields from mixin"""
        warehouse = Warehouse.objects.create(
            name="Audit Test Warehouse",
            code="AUDIT01",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check audit fields are set
        self.assertEqual(warehouse.created_by, self.user)
        self.assertEqual(warehouse.updated_by, self.user)
        self.assertIsNotNone(warehouse.created_at)
        self.assertIsNotNone(warehouse.updated_at)
        self.assertEqual(warehouse.version, 1)

    def test_code_normalization(self):
        """Test that warehouse code is normalized to uppercase"""
        warehouse = Warehouse(
            name="Normalization Test",
            code="lower01",  # lowercase
            created_by=self.user,
            updated_by=self.user
        )
        warehouse.save()
        
        # Should be converted to uppercase
        self.assertEqual(warehouse.code, "LOWER01")

    def test_string_representation(self):
        """Test warehouse string representation"""
        warehouse = Warehouse.objects.create(
            name="Display Test Warehouse",
            code="DISP01",
            created_by=self.user,
            updated_by=self.user
        )
        
        expected = "DISP01 - Display Test Warehouse"
        self.assertEqual(str(warehouse), expected)
        self.assertEqual(warehouse.get_display_name(), expected)

    def test_field_length_validation(self):
        """Test field length validations"""
        # Long address
        long_address = "A" * 501
        warehouse = Warehouse(
            name="Test Warehouse",
            code="TEST01",
            address=long_address,
            created_by=self.user,
            updated_by=self.user
        )
        is_valid, errors = warehouse.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("500 characters", str(errors))

        # Long note
        long_note = "A" * 1001
        warehouse.address = "Valid address"
        warehouse.note = long_note
        is_valid, errors = warehouse.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("1000 characters", str(errors))
