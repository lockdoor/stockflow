# StockMovementItem Model Refactor

## Overview
Comprehensive refactoring of the `StockMovementItem` model to improve code quality, consistency, and maintainability.

## Key Changes

### 1. **Field Name Standardization**
- `item` → `item_sku` (consistency with other models)
- `lot` → `lot_number` (more descriptive)
- `expired` → `expiry_date` (proper naming convention)
- `note` → `note` (changed from CharField to TextField for longer notes)

### 2. **Enhanced Documentation**
- Added comprehensive docstrings
- Detailed field help_text
- Business rules documentation
- Usage examples

### 3. **Improved Validation**
- Quantity must be positive (> 0)
- Expiry date cannot be in the past
- Full model validation in save method
- Better error messages using ValidationError

### 4. **Business Logic Enhancements**

#### Properties Added:
- `is_inbound` - Check if movement is stock in
- `is_outbound` - Check if movement is stock out  
- `can_modify` - Check if item can be modified
- `get_display_name()` - Formatted display name

#### Protection Features:
- Cannot modify/delete items in CONFIRMED movements
- Optimistic locking with better error messages
- Proper exception handling

### 5. **Database Optimizations**

#### Indexing:
```python
indexes = [
    models.Index(fields=['stock_movement', 'item_sku']),
    models.Index(fields=['movement_type', 'created_at']),
    models.Index(fields=['lot_number']),
]
```

#### Ordering:
```python
ordering = ['-created_at', 'item_sku__sku_code']
```

#### Relationships:
- `related_name='movement_items'` for better query access
- Proper foreign key constraints

### 6. **Choice Field Improvements**
```python
class MovementType(models.TextChoices):
    IN = 'IN', 'Stock In'
    OUT = 'OUT', 'Stock Out'
```

## Migration Strategy

### Step 1: Schema Migration
```bash
python manage.py makemigrations inventory --name refactor_stock_movement_item
```

### Step 2: Data Migration
```bash
python manage.py makemigrations inventory --empty --name migrate_field_names
```

Data migration copies:
- `item` → `item_sku`
- `lot` → `lot_number`
- `expired` → `expiry_date`

### Step 3: Apply Migrations
```bash
python manage.py migrate inventory
```

## Template Updates

### Before:
```html
<td>{{ item.item.sku_code }}</td>
<td>{{ item.lot }}</td>
<td>{{ item.expired }}</td>
```

### After:
```html
<td>{{ item.item_sku.sku_code }}</td>
<td>{{ item.lot_number|default:"-" }}</td>
<td>{{ item.expiry_date|date:"M d, Y"|default:"-" }}</td>
<td>
    <span class="badge {% if item.is_inbound %}badge-success{% else %}badge-warning{% endif %}">
        {{ item.get_movement_type_display }}
    </span>
</td>
```

## Form Updates

Forms need to be updated to use new field names:
```python
class StockMovementItemForm(forms.ModelForm):
    class Meta:
        model = StockMovementItem
        fields = ['item_sku', 'movement_type', 'quantity', 'lot_number', 'expiry_date', 'note']
```

## Testing

Comprehensive test suite covering:
- ✅ Model creation and validation
- ✅ Business logic constraints
- ✅ Optimistic locking
- ✅ Field validation
- ✅ Database constraints
- ✅ Property methods
- ✅ String representations

### Run Tests:
```bash
python manage.py test inventory.tests.test_models.test_stock_movement_item
```

## Benefits

### 1. **Consistency**
- Uniform naming conventions across models
- Consistent with Django best practices
- Better integration with other models

### 2. **Maintainability**
- Clear documentation and docstrings
- Proper separation of concerns
- Easier to understand and modify

### 3. **Performance**
- Database indexes for common queries
- Optimized foreign key relationships
- Better query patterns

### 4. **User Experience**
- Better error messages
- Visual indicators for movement types
- Improved form validation

### 5. **Data Integrity**
- Stronger validation rules
- Business logic enforcement
- Optimistic locking protection

## Breaking Changes

### Models:
- Field names changed (requires migration)
- Related name changed to `movement_items`

### Templates:
- Update field references
- Use new property methods

### Forms:
- Update field names in forms
- Adjust validation logic

### Views:
- Update form handling
- Adjust query patterns

## Backward Compatibility

- Data migration preserves existing data
- Reverse migration available
- Template fallbacks where appropriate

## Future Enhancements

1. **Stock Level Tracking**: Add real-time stock calculations
2. **Batch Processing**: Support for bulk movement operations
3. **Cost Tracking**: Add cost per unit and total cost fields
4. **Serial Number Tracking**: Track individual items by serial numbers
5. **Location Tracking**: Add bin/location within warehouse
