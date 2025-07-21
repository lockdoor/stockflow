# StockFlow Common Components Architecture

## Overview

The `common` app provides shared utilities, mixins, and base classes that can be used across all StockFlow applications. This promotes code reuse, consistency, and maintainability.

## File Structure

```
stockflow/
├── common/                          # Shared components app
│   ├── __init__.py
│   ├── apps.py                     # App configuration
│   ├── mixins/                     # Reusable model mixins
│   │   ├── __init__.py
│   │   ├── auditable.py           # AuditableMixin - audit fields & optimistic locking
│   │   ├── status.py              # StatusMixin - active/inactive management
│   │   └── validatable.py         # ValidatableMixin - validation framework
│   ├── validators/                 # Base validation classes
│   │   ├── __init__.py
│   │   └── base_validators.py     # Common validator patterns
│   └── utils/                     # Utility functions (future)
│       └── __init__.py
├── inventory/
│   ├── mixins/                    # Inventory-specific mixins (if any)
│   ├── validators/
│   │   └── warehouse_validators.py # Uses common base validators
│   └── models/
│       └── warehouse.py           # Uses common mixins
├── catalog/
│   ├── mixins/                    # Catalog-specific mixins (if any)
│   ├── validators/
│   │   └── item_validators.py     # Will use common base validators
│   └── models/
│       └── item.py                # Can use common mixins
└── ...
```

## Common Mixins

### AuditableMixin
Provides audit fields and optimistic locking:
- `created_at`, `created_by`
- `updated_at`, `updated_by`
- `version` (optimistic locking)
- `history` (simple-history tracking)

**Usage:**
```python
from common.mixins.auditable import AuditableMixin

class MyModel(AuditableMixin, models.Model):
    # Your fields...
    pass
```

### StatusMixin
Provides status management:
- `is_active` field
- `activate()`, `deactivate()`, `toggle_status()` methods
- `status_display` property
- `can_deactivate()` method (override for business rules)

**Usage:**
```python
from common.mixins.status import StatusMixin

class MyModel(StatusMixin, models.Model):
    # Your fields...
    
    def can_deactivate(self):
        # Override for custom business rules
        return True, ""
```

### ValidatableMixin
Provides validation framework:
- `get_validators()` method to return list of validators
- `clean()` method that runs all validators
- `is_valid()` method for non-exception validation

**Usage:**
```python
from common.mixins.validatable import ValidatableMixin

class MyModel(ValidatableMixin, models.Model):
    # Your fields...
    
    def get_validators(self):
        return [
            MyValidator1(self),
            MyValidator2(self),
        ]
```

## Base Validators

### Available Base Validators
- `RequiredFieldValidator` - Check required fields
- `LengthValidator` - Check min/max length
- `RegexValidator` - Pattern matching
- `UniqueFieldValidator` - Uniqueness constraints
- `CodeFormatValidator` - Alphanumeric codes

**Usage:**
```python
from common.validators.base_validators import RequiredFieldValidator, LengthValidator

class MyFieldValidator:
    def __init__(self, instance):
        self.instance = instance
    
    def validate(self):
        validators = [
            RequiredFieldValidator(self.instance, 'name'),
            LengthValidator(self.instance, 'name', min_length=2, max_length=100)
        ]
        
        for validator in validators:
            error = validator.validate()
            if error:
                return error
        return None
```

## Benefits

### Code Reuse
- Common functionality written once, used everywhere
- Consistent behavior across all models

### Maintainability
- Changes to audit/validation logic in one place
- Easy to extend and modify

### Testability
- Mixins and validators can be tested independently
- Easier to mock and test complex scenarios

### Consistency
- Same validation patterns across all apps
- Consistent error messages and behavior

## Migration Strategy

1. **Phase 1**: Create common app with base mixins ✅
2. **Phase 2**: Refactor inventory models to use common mixins ✅
3. **Phase 3**: Refactor catalog models to use common mixins
4. **Phase 4**: Add more common utilities as needed

## Usage Guidelines

### When to use Common Components
- Audit fields (created_at, updated_at, etc.)
- Status management (active/inactive)
- Basic validation patterns
- Cross-app utilities

### When to create App-specific Components
- Business logic specific to one domain
- Complex validations that are domain-specific
- App-specific mixins that don't apply elsewhere

## Example: Complete Model Implementation

```python
# inventory/models/warehouse.py
from django.db import models
from common.mixins.auditable import AuditableMixin
from common.mixins.status import StatusMixin
from common.mixins.validatable import ValidatableMixin
from inventory.validators.warehouse_validators import (
    WarehouseNameValidator,
    WarehouseCodeValidator,
    WarehouseBusinessRulesValidator
)

class Warehouse(AuditableMixin, StatusMixin, ValidatableMixin, models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    # ... other fields
    
    def get_validators(self):
        return [
            WarehouseNameValidator(self),
            WarehouseCodeValidator(self),
            WarehouseBusinessRulesValidator(self)
        ]
    
    def can_deactivate(self):
        # Custom business logic
        if self.stock_movements.filter(status='DRAFT').exists():
            return False, "Has active stock movements"
        return True, ""
```

This architecture ensures clean, maintainable, and reusable code across the entire StockFlow application.
