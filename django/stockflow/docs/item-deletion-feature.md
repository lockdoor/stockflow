# Item Deletion Feature Documentation

## Overview
This document describes the implementation of the item deletion feature with safety checks to prevent deletion of items that are referenced by other records in the system.

## Features

### 1. Reference Detection
The system automatically checks if an item is referenced by other entities before allowing deletion:

- **BOM References**: Items used as parent or component in BOMs
- **Stock Movements**: Items with historical stock movement records  
- **Stock Records**: Items with current stock levels
- **Production Results**: Items produced in production processes
- **Material Reservations**: Items with material reservation records
- **Stock Alerts**: Items with configured stock alerts

### 2. Smart Delete Button
The item detail page shows context-aware delete functionality:

- **Deletable Items**: Shows active delete button with link to confirmation page
- **Non-deletable Items**: Shows disabled delete button with tooltip explaining why deletion is blocked

### 3. Confirmation Page
A comprehensive confirmation page that:

- **Safe Items**: Shows deletion confirmation with item details and requires user acknowledgment
- **Blocked Items**: Shows detailed list of blocking references with counts and descriptions

## Implementation Details

### Model Changes

#### ItemSKU.can_be_deleted()
```python
def can_be_deleted(self):
    """
    Check if this item can be deleted (not referenced by other entities)
    Returns tuple (can_delete: bool, blocking_references: list)
    """
```

Returns:
- `can_delete` (bool): Whether the item can be safely deleted
- `blocking_references` (list): List of dictionaries containing:
  - `type`: Type of blocking reference
  - `count`: Number of blocking records
  - `description`: Human-readable description

### View Changes

#### ItemDetailView
Enhanced to include deletion capability information:
```python
# Add delete capability info
can_delete, blocking_references = self.object.can_be_deleted()
context['can_delete'] = can_delete
context['blocking_references'] = blocking_references
```

#### ItemDeleteView (New)
- Handles GET requests: Shows confirmation page
- Handles POST requests: Performs deletion with safety checks
- Requires `catalog.delete_itemsku` permission
- Redirects to item list on successful deletion
- Redirects to item detail with error message if deletion is blocked

### URL Configuration
```python
path('items/<int:pk>/delete/', ItemDeleteView.as_view(), name='item-delete'),
```

### Template Changes

#### item-detail.html
Enhanced Quick Actions section with conditional delete button:
```html
{% if can_delete %}
<a href="{% url 'catalog:item-delete' item.id %}" class="btn btn-outline-danger">
    <i class="bi bi-trash me-2"></i>Delete Item
</a>
{% else %}
<button type="button" class="btn btn-outline-danger" disabled 
        data-bs-toggle="tooltip" 
        title="Cannot delete: Item is referenced by other records">
    <i class="bi bi-trash me-2"></i>Delete Item
</button>
{% endif %}
```

#### item-delete-confirm.html (New)
Complete confirmation page with:
- Warning messages for irreversible action
- Item details display
- Blocking references list (if any)
- Confirmation checkbox requirement
- Safe deletion process

## Security Features

### Permission-Based Access
- Requires `catalog.delete_itemsku` permission
- Login required for all deletion-related views

### Data Integrity Protection
- Prevents deletion of items with existing references
- Comprehensive reference checking across all apps
- Safe handling of missing/disabled apps

### User Experience
- Clear feedback on why deletion is blocked
- Detailed reference information
- Confirmation requirement for destructive actions

## Usage Examples

### Deleting an Unused Item
1. Navigate to item detail page
2. Click "Delete Item" button in Quick Actions
3. Review item details on confirmation page
4. Check confirmation checkbox
5. Click "Delete Item" to confirm

### Attempting to Delete Referenced Item
1. Navigate to item detail page
2. See disabled "Delete Item" button with tooltip
3. Or click enabled button to see blocking references
4. Review blocking references list
5. Remove references before attempting deletion again

## Error Handling

### Validation Errors
- Items with references cannot be deleted
- Clear error messages explaining blocking references
- Graceful handling of app availability checks

### Permission Errors  
- 403 Forbidden for users without delete permission
- Proper authentication checks

### Exception Handling
- Safe handling of missing related objects
- Graceful degradation when apps are unavailable
- Database transaction safety

## Testing

### Unit Tests
Comprehensive test suite covering:
- Reference detection accuracy
- View behavior with deletable/non-deletable items
- Permission requirements
- Successful deletion workflow
- Blocked deletion handling

### Test Files
- `catalog/tests/item/test_item_deletion.py`: Complete test suite

## API Reference

### ItemSKU Methods

#### can_be_deleted()
```python
can_delete, blocking_references = item.can_be_deleted()
```

**Returns:**
- `tuple`: (can_delete: bool, blocking_references: list)

**blocking_references format:**
```python
[
    {
        'type': 'BOM (as parent)',
        'count': 3,
        'description': 'This item has BOM components'
    },
    # ... more references
]
```

### URL Names
- `catalog:item-delete`: Delete confirmation page
- Used with item ID: `{% url 'catalog:item-delete' item.id %}`

## Future Enhancements

### Potential Improvements
1. **Bulk Reference Removal**: Tools to help remove blocking references
2. **Reference Details**: Links to specific blocking records
3. **Cascade Options**: Optional cascade deletion for certain reference types
4. **Audit Trail**: Enhanced logging of deletion attempts
5. **Archive Instead**: Option to archive items instead of deleting

### Performance Considerations
- Reference checking queries could be optimized for large datasets
- Consider caching reference counts for frequently accessed items
- Batch processing for bulk operations

## Troubleshooting

### Common Issues
1. **Button Not Showing**: Check user permissions
2. **Always Disabled**: Verify reference detection logic
3. **Template Errors**: Ensure proper context variables
4. **Permission Denied**: Add required permissions to user/group

### Debug Tips
- Use Django admin to inspect item references
- Check server logs for validation errors
- Test with minimal test data first
- Verify app installation and configuration