# StockMovementItem Validation Rules

## Overview
Comprehensive validation system for StockMovementItem model to ensure data integrity and business rule compliance.

## Validation Categories

### 1. **Item SKU Validation** (`_validate_item_sku`)
- ✅ **Required Field**: Item SKU must be provided
- ✅ **Status Check**: Only ACTIVE items can be moved
- ✅ **Clear Error Messages**: Shows current status if inactive

```python
def _validate_item_sku(self) -> str | None:
    if not self.item_sku:
        return "Item SKU is required"
    if self.item_sku.status != ItemSKU.Status.ACTIVE:
        return f"Cannot move inactive item SKU ({self.item_sku.get_status_display()})"
```

### 2. **Quantity Validation** (`_validate_quantity`)
- ✅ **Required Field**: Quantity must be provided
- ✅ **Positive Values**: Must be greater than zero
- ✅ **Decimal Places**: Maximum 2 decimal places
- ✅ **Maximum Limit**: Prevents unreasonably large quantities (999,999.99)

```python
def _validate_quantity(self) -> str | None:
    if self.quantity is None:
        return "Quantity is required"
    if self.quantity <= 0:
        return "Quantity must be greater than zero"
    if self.quantity.as_tuple().exponent < -2:
        return "Quantity cannot have more than 2 decimal places"
    if self.quantity > 999999.99:
        return f"Quantity cannot exceed 999,999.99"
```

### 3. **Expiry Date Validation** (`_validate_expiry_date`)
- ✅ **Past Date Check**: Cannot be in the past
- ✅ **Future Limit**: Cannot be more than 50 years in the future
- ✅ **Reasonable Range**: Prevents data entry errors

```python
def _validate_expiry_date(self) -> str | None:
    if self.expiry_date and self.expiry_date < timezone.now().date():
        return "Expiry date cannot be in the past"
    if self.expiry_date:
        max_future_date = timezone.now().date().replace(year=timezone.now().year + 50)
        if self.expiry_date > max_future_date:
            return "Expiry date cannot be more than 50 years in the future"
```

### 4. **Movement Type Consistency** (`_validate_movement_type_consistency`)
- ✅ **Parent Movement Check**: Stock movement must exist
- ✅ **Type Alignment**: Movement type should align with parent movement
  - RECEIPT → typically IN items
  - ISSUE → typically OUT items
- ✅ **Business Logic**: Ensures logical consistency

### 5. **Lot Number Validation** (`_validate_lot_number`)
- ✅ **Format Check**: Alphanumeric with specific special characters
- ✅ **Length Limit**: Maximum 64 characters
- ✅ **Required for Certain Types**: RAW and PACKAGE items require lot numbers
- ✅ **Pattern Matching**: Uses regex for format validation

```python
def _validate_lot_number(self) -> str | None:
    if self.lot_number:
        if not re.match(r'^[A-Za-z0-9\-_/]+$', self.lot_number):
            return "Lot number can only contain letters, numbers, hyphens, underscores, and forward slashes"
        if len(self.lot_number) > 64:
            return "Lot number cannot exceed 64 characters"
    
    if self.item_sku and self.item_sku.item_type in [ItemSKU.ItemType.RAW, ItemSKU.ItemType.PACKAGE]:
        if not self.lot_number:
            return f"Lot number is required for {self.item_sku.get_item_type_display()} items"
```

### 6. **Stock Availability** (`_validate_outbound_quantity`)
- ✅ **Outbound Only**: Only validates OUT movements
- ✅ **Draft Skip**: Skips validation for draft movements
- 🚧 **Stock Level Check**: Framework for future stock level validation
- 🚧 **Available Stock**: Integration point for inventory tracking

### 7. **Warehouse Compatibility** (`_validate_warehouse_item_compatibility`)
- ✅ **Warehouse Status**: Cannot move to/from inactive warehouses
- 🚧 **Item Compatibility**: Framework for warehouse-specific item rules
- 🚧 **Special Requirements**: Temperature control, hazardous materials, etc.

### 8. **Duplicate Prevention** (`_validate_duplicate_item_in_movement`)
- ✅ **Same Movement Check**: Prevents duplicate items in same movement
- ✅ **Lot Consideration**: Includes lot number in uniqueness check
- ✅ **Update Safe**: Excludes current item when updating
- ✅ **Clear Messaging**: Specific error messages

### 9. **Note Field Validation** (`_validate_note_length`)
- ✅ **Length Limit**: Maximum 500 characters
- ✅ **Optional Field**: Note is not required

### 10. **Complex Business Rules** (`_validate_business_rules`)
- 🚧 **Temperature Control**: Items requiring special handling
- 🚧 **Date Consistency**: Movement dates vs creation dates
- 🚧 **Special Requirements**: Extensible for future business rules

## Implementation Benefits

### 1. **Data Integrity**
- Prevents invalid data entry
- Ensures business rule compliance
- Maintains database consistency

### 2. **User Experience**
- Clear, specific error messages
- Early validation feedback
- Prevents common mistakes

### 3. **Maintainability**
- Modular validation methods
- Easy to add new rules
- Clear separation of concerns

### 4. **Performance**
- Efficient validation order
- Database queries only when needed
- Minimal overhead

### 5. **Extensibility**
- Framework for future rules
- Easy to modify existing rules
- Supports complex business logic

## Usage Examples

### Valid Movement Item
```python
movement_item = StockMovementItem(
    stock_movement=receipt_movement,
    item_sku=active_item,
    movement_type=StockMovementItem.MovementType.IN,
    quantity=Decimal('10.50'),
    lot_number='LOT2025001',
    expiry_date=date.today() + timedelta(days=365),
    note='Received from supplier ABC'
)
movement_item.full_clean()  # Validates all rules
movement_item.save()
```

### Validation Errors
```python
# Invalid quantity
movement_item.quantity = Decimal('-5.00')
# Raises: "Quantity must be greater than zero"

# Invalid expiry date
movement_item.expiry_date = date.today() - timedelta(days=1)
# Raises: "Expiry date cannot be in the past"

# Invalid lot number format
movement_item.lot_number = 'LOT@2025#001'
# Raises: "Lot number can only contain letters, numbers..."
```

## Testing Strategy

Each validation method should have comprehensive tests:

```python
def test_quantity_validation(self):
    # Test zero quantity
    # Test negative quantity
    # Test too many decimal places
    # Test maximum quantity exceeded
    # Test valid quantities

def test_lot_number_validation(self):
    # Test invalid characters
    # Test too long
    # Test required for RAW items
    # Test valid lot numbers
```

## Future Enhancements

### 1. **Stock Level Integration**
- Real-time stock checking
- Available quantity validation
- Reservation system integration

### 2. **Advanced Business Rules**
- Item compatibility matrices
- Warehouse capacity limits
- Regulatory compliance checks

### 3. **Performance Optimization**
- Batch validation for bulk operations
- Cached validation results
- Async validation for complex rules

### 4. **Integration Features**
- External system validation
- API-based rule engines
- Dynamic rule configuration

## Error Handling

All validation methods return:
- `None` for valid data
- `str` with error message for invalid data

The `clean()` method collects all errors and raises a single `ValidationError` with combined messages, providing comprehensive feedback to users.
