```mermaid
classDiagram
    %% Base Django Model
    class Model {
        +save()
        +delete()
        +clean()
        +full_clean()
    }
    
    %% Common Mixins
    class AuditableMixin {
        +DateTimeField created_at
        +ForeignKey created_by
        +DateTimeField updated_at 
        +ForeignKey updated_by
        +PositiveIntegerField version
        +save()*
        +set_audit_fields()
        +increment_version()
    }
    
    class StatusMixin {
        +BooleanField is_active
        +save()*
        +activate()
        +deactivate()
        +toggle_status()
        +validate_status_change()
    }
    
    class ValidatableMixin {
        +save()*
        +get_validators()
        +run_validators()
        +handle_validation_errors()
    }
    
    %% Warehouse Validators
    class WarehouseNameValidator {
        +warehouse_instance
        +validate()
        -_check_required()
        -_check_length()
        -_check_unique()
    }
    
    class WarehouseCodeValidator {
        +warehouse_instance
        +validate()
        -_check_required()
        -_check_format()
        -_check_unique()
    }
    
    class WarehouseBusinessRulesValidator {
        +warehouse_instance
        +validate()
        -_check_can_deactivate()
        -_check_field_lengths()
    }
    
    %% Main Warehouse Model
    class Warehouse {
        +CharField name
        +CharField code
        +TextField address
        +TextField note
        +save()*
        +get_validators()
        +can_deactivate()
        +get_display_name()
        +has_stock_movements
        +active_movements_count
    }
    
    %% Inheritance relationships
    Model <|-- AuditableMixin : extends
    Model <|-- StatusMixin : extends
    Model <|-- ValidatableMixin : extends
    
    AuditableMixin <|-- Warehouse : inherits
    StatusMixin <|-- Warehouse : inherits
    ValidatableMixin <|-- Warehouse : inherits
    Model <|-- Warehouse : inherits
    
    %% Composition relationships (validators)
    Warehouse --> WarehouseNameValidator : uses
    Warehouse --> WarehouseCodeValidator : uses
    Warehouse --> WarehouseBusinessRulesValidator : uses
    
    %% Method Resolution Order (MRO)
    note for Warehouse "MRO: Warehouse → AuditableMixin → StatusMixin → ValidatableMixin → Model"
    
    %% Mixin responsibilities
    note for AuditableMixin "Handles: audit fields, version control, optimistic locking"
    note for StatusMixin "Handles: is_active field, status validation, activation/deactivation"
    note for ValidatableMixin "Handles: clean() integration, validator orchestration"
    note for Warehouse "Handles: business logic, field normalization, custom validation"
    
    %% Validator responsibilities
    note for WarehouseNameValidator "Validates: required, length (2-100), uniqueness"
    note for WarehouseCodeValidator "Validates: required, format (alphanumeric), uniqueness"
    note for WarehouseBusinessRulesValidator "Validates: deactivation rules, field lengths"

    %% Field inheritance visualization
    class FieldInheritance {
        <<interface>>
        From AuditableMixin:
        - created_at: DateTimeField
        - created_by: ForeignKey(User)
        - updated_at: DateTimeField  
        - updated_by: ForeignKey(User)
        - version: PositiveIntegerField
        
        From StatusMixin:
        - is_active: BooleanField
        
        From Warehouse:
        - name: CharField(100)
        - code: CharField(10, unique=True)
        - address: TextField(blank=True)
        - note: TextField(blank=True)
    }
    
    Warehouse --> FieldInheritance : contains
```

## Warehouse Model Class Diagram

This diagram shows the inheritance hierarchy and relationships of the Warehouse model:

### **Inheritance Chain (MRO - Method Resolution Order):**
1. **Warehouse** (main model)
2. **AuditableMixin** (audit fields & version control)
3. **StatusMixin** (status management)
4. **ValidatableMixin** (validation orchestration)
5. **Model** (Django base model)

### **Mixin Responsibilities:**

#### 🔍 **AuditableMixin**
- Provides audit fields: `created_at`, `created_by`, `updated_at`, `updated_by`, `version`
- Handles optimistic locking via version field
- Automatically sets audit fields on save

#### 📊 **StatusMixin**
- Provides `is_active` field
- Handles activation/deactivation logic
- Validates status changes

#### ✅ **ValidatableMixin**
- Integrates with Django's `clean()` method
- Orchestrates multiple validators
- Handles validation error formatting

#### 🏭 **Warehouse Model**
- Contains core business fields
- Implements domain-specific business logic
- Normalizes data (code to uppercase)
- Provides helper methods and properties

### **Validation Strategy:**
The Warehouse uses **composition over inheritance** for validators:
- **WarehouseNameValidator**: Name requirements & uniqueness
- **WarehouseCodeValidator**: Code format & uniqueness  
- **WarehouseBusinessRulesValidator**: Business constraints

### **Key Benefits:**
1. **Single Responsibility**: Each mixin has one clear purpose
2. **Reusability**: Mixins can be used by other models
3. **Testability**: Each component can be tested independently
4. **Maintainability**: Changes isolated to specific concerns
5. **Domain Boundaries**: Validators stay within inventory domain
