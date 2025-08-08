# Toast Notification System

A comprehensive guide to the centralized toast notification system in StockFlow, implementing Bootstrap 5 toasts with Django's messages framework.

## Overview

The toast notification system provides a modern, non-intrusive way to display user feedback messages across the application. It replaces traditional alert boxes with elegant toast notifications that appear in the top-right corner of the screen.

## Architecture

### Components
- **Base Template Integration**: Centralized toast container in `base-dashboard-header.html`
- **Django Messages Framework**: Backend message handling and categorization
- **Bootstrap 5 Toasts**: Frontend toast components with auto-dismiss functionality
- **JavaScript Controller**: Automatic toast initialization and display

### Message Types Supported
- **Success** (`success`) - Green background with check-circle icon
- **Error** (`error`) - Red background with exclamation-triangle icon  
- **Warning** (`warning`) - Yellow background with exclamation-triangle icon
- **Info** (`info`) - Blue background with info-circle icon
- **Default** - Primary blue background with info-circle icon

## Implementation

### Base Template Structure

The toast container is implemented in `templates/base-dashboard-header.html`:

```html
<!-- Toast Container -->
<div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 1080;">
    {% if messages %}
        {% for message in messages %}
            <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" 
                 data-bs-autohide="true" data-bs-delay="5000">
                <div class="toast-header">
                    {% if message.tags == 'error' %}
                        <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
                        <strong class="me-auto">Error</strong>
                    {% elif message.tags == 'warning' %}
                        <i class="bi bi-exclamation-triangle-fill text-warning me-2"></i>
                        <strong class="me-auto">Warning</strong>
                    {% elif message.tags == 'success' %}
                        <i class="bi bi-check-circle-fill text-success me-2"></i>
                        <strong class="me-auto">Success</strong>
                    {% else %}
                        <i class="bi bi-info-circle-fill text-primary me-2"></i>
                        <strong class="me-auto">Info</strong>
                    {% endif %}
                    <small class="text-body-secondary">now</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    {{ message }}
                </div>
            </div>
        {% endfor %}
    {% endif %}
</div>
```

### JavaScript Initialization

Automatic toast display is handled by JavaScript in the base template:

```javascript
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Auto-show all toasts
    var toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(function(toastElement) {
        var toast = new bootstrap.Toast(toastElement);
        toast.show();
    });
});
</script>
```

## Usage Examples

### Backend (Django Views)

#### Basic Success Message
```python
from django.contrib import messages

def stock_movement_create_view(request):
    # ... view logic ...
    messages.success(request, 'Stock movement created successfully!')
    return redirect('inventory:stock-movement-detail', pk=stock_movement.pk)
```

#### Error Message
```python
def stock_movement_update_view(request):
    try:
        # ... update logic ...
        messages.success(request, 'Stock movement updated successfully!')
    except ValidationError as e:
        messages.error(request, f'Validation error: {e}')
    except Exception as e:
        messages.error(request, 'An unexpected error occurred. Please try again.')
```

#### Warning Message
```python
def stock_movement_confirm_view(request):
    if stock_movement.status != 'DRAFT':
        messages.warning(request, 'Only draft movements can be confirmed.')
        return redirect('inventory:stock-movement-detail', pk=stock_movement.pk)
```

#### Info Message
```python
def stock_movement_list_view(request):
    if not request.user.has_perm('inventory.view_stockmovement'):
        messages.info(request, 'Contact administrator for access to stock movements.')
```

### Frontend (Template Usage)

#### Form Validation Messages
```python
# In views.py
def form_invalid(self, form):
    messages.error(self.request, 'Please correct the errors below.')
    return super().form_invalid(form)
```

#### Bulk Operations
```python
def bulk_confirm_movements(request):
    confirmed_count = 0
    failed_count = 0
    
    for movement_id in request.POST.getlist('movement_ids'):
        try:
            # ... confirm logic ...
            confirmed_count += 1
        except Exception:
            failed_count += 1
    
    if confirmed_count > 0:
        messages.success(request, f'{confirmed_count} movements confirmed successfully.')
    if failed_count > 0:
        messages.warning(request, f'{failed_count} movements failed to confirm.')
```

## Configuration

### Toast Behavior Settings

The toast system uses the following default settings:

```javascript
// Auto-hide after 5 seconds
data-bs-delay="5000"

// Enable auto-hide
data-bs-autohide="true"

// Position: top-right corner
position-fixed top-0 end-0

// Z-index for proper layering
style="z-index: 1080;"
```

### Customizing Toast Duration

To change toast display duration, modify the `data-bs-delay` attribute:

```html
<!-- 3-second display -->
<div class="toast" data-bs-delay="3000">

<!-- 10-second display -->
<div class="toast" data-bs-delay="10000">

<!-- Disable auto-hide (manual close only) -->
<div class="toast" data-bs-autohide="false">
```

### Custom Message Tags

Django's messages framework can use custom tags:

```python
from django.contrib import messages

# Custom level
messages.add_message(request, messages.INFO, 'Custom info message', extra_tags='custom')

# In template, check for custom tags
{% if message.tags == 'custom' %}
    <i class="bi bi-star-fill text-warning me-2"></i>
    <strong class="me-auto">Special</strong>
{% endif %}
```

## Best Practices

### Message Content Guidelines

1. **Be Concise**: Keep messages brief and actionable
   ```python
   # Good
   messages.success(request, 'Movement saved successfully.')
   
   # Avoid
   messages.success(request, 'Your stock movement has been successfully saved to the database and is now available for viewing in the system.')
   ```

2. **Use Appropriate Levels**:
   - `success`: Confirmed successful operations
   - `error`: Critical errors requiring user action
   - `warning`: Important notices that don't block workflow
   - `info`: General information or tips

3. **Provide Context**:
   ```python
   # Good
   messages.error(request, 'Cannot delete movement #123: Contains confirmed items.')
   
   # Less helpful
   messages.error(request, 'Delete failed.')
   ```

### Performance Considerations

1. **Limit Message Count**: Avoid displaying too many toasts simultaneously
   ```python
   # Clear existing messages before adding new ones if needed
   storage = messages.get_messages(request)
   storage.used = True  # Mark as used to clear
   messages.success(request, 'New important message')
   ```

2. **Message Persistence**: Messages are session-based and survive redirects
   ```python
   # Messages persist through redirects
   messages.success(request, 'Created successfully!')
   return redirect('detail_view')  # Message will display on detail page
   ```

### Accessibility Features

The toast system includes accessibility features:

```html
<!-- Screen reader support -->
role="alert" 
aria-live="assertive" 
aria-atomic="true"

<!-- Keyboard navigation -->
<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close">
```

## Migration from Alert Messages

### Before (Alert-based)
```html
<!-- Old alert implementation -->
{% if messages %}
    {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    {% endfor %}
{% endif %}
```

### After (Toast-based)
```html
<!-- New implementation automatically handled by base template -->
<!-- No template changes needed in individual pages -->
```

### View Changes
```python
# No changes needed in views - same messages framework
messages.success(request, 'Operation completed successfully!')
```

## Troubleshooting

### Common Issues

#### 1. Toasts Not Appearing
**Cause**: Bootstrap JavaScript not loaded or toast container missing
**Solution**: Ensure Bootstrap 5 JS is included and base template extends correctly

#### 2. Multiple Duplicate Toasts
**Cause**: Multiple template inheritance or JavaScript initialization
**Solution**: Remove duplicate toast containers from child templates

#### 3. Toast Styling Issues
**Cause**: CSS conflicts or missing Bootstrap Icons
**Solution**: Verify Bootstrap CSS and Icons are properly loaded

#### 4. Accessibility Warnings
**Cause**: Missing ARIA attributes
**Solution**: Ensure all toasts include proper accessibility attributes

### Debug Mode

To debug toast functionality, add console logging:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    var toastElements = document.querySelectorAll('.toast');
    console.log('Found toasts:', toastElements.length);
    
    toastElements.forEach(function(toastElement) {
        var toast = new bootstrap.Toast(toastElement);
        console.log('Showing toast:', toastElement);
        toast.show();
    });
});
```

## Browser Compatibility

The toast system supports:
- **Modern Browsers**: Chrome 88+, Firefox 84+, Safari 14+, Edge 88+
- **Bootstrap 5 Requirements**: IE 11+ with polyfills
- **JavaScript**: ES6+ features used (consider transpilation for older browsers)

## Related Documentation

- [Django Messages Framework](https://docs.djangoproject.com/en/4.2/ref/contrib/messages/)
- [Bootstrap 5 Toasts](https://getbootstrap.com/docs/5.3/components/toasts/)
- [Template Structure Guidelines](./template-structure-guidelines.md)
- [Icon Design System](./icon-design-system.md)

## Version History

### v2.0 (Current)
- Centralized toast container in base template
- Removed duplicate implementations
- Enhanced accessibility support
- Added comprehensive documentation

### v1.0 (Legacy)
- Individual template implementations
- Basic Bootstrap toast integration
- Limited customization options

---

*Last Updated: August 8, 2025*
*Author: StockFlow Development Team*
