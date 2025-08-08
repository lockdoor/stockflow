# Toast Notifications Quick Reference

A quick reference guide for using toast notifications in StockFlow.

## Quick Start

### 1. Basic Usage in Views
```python
from django.contrib import messages

# Success message
messages.success(request, 'Operation completed successfully!')

# Error message  
messages.error(request, 'Something went wrong.')

# Warning message
messages.warning(request, 'Please review your input.')

# Info message
messages.info(request, 'Additional information available.')
```

### 2. Templates
**No setup required!** Toast container is automatically included in `base-dashboard-header.html`.

Just ensure your template extends the base:
```html
{% extends "base-dashboard-header.html" %}
```

## Message Types & Icons

| Type | Class | Icon | Use Case |
|------|-------|------|----------|
| `success` | `text-success` | `bi-check-circle-fill` | Successful operations |
| `error` | `text-danger` | `bi-exclamation-triangle-fill` | Errors, failures |
| `warning` | `text-warning` | `bi-exclamation-triangle-fill` | Warnings, cautions |
| `info` | `text-primary` | `bi-info-circle-fill` | Information, tips |

## Common Patterns

### Form Validation
```python
def form_valid(self, form):
    # ... save logic ...
    messages.success(self.request, f'{self.model.__name__} saved successfully!')
    return super().form_valid(form)

def form_invalid(self, form):
    messages.error(self.request, 'Please correct the errors below.')
    return super().form_invalid(form)
```

### Exception Handling
```python
try:
    # ... operation ...
    messages.success(request, 'Stock movement confirmed!')
except ValidationError as e:
    messages.error(request, f'Validation failed: {e}')
except Exception as e:
    messages.error(request, 'An unexpected error occurred.')
```

### Bulk Operations
```python
success_count = 0
error_count = 0

for item in items:
    try:
        # ... process item ...
        success_count += 1
    except Exception:
        error_count += 1

if success_count > 0:
    messages.success(request, f'{success_count} items processed successfully.')
if error_count > 0:
    messages.warning(request, f'{error_count} items failed to process.')
```

### Conditional Messages
```python
if user.has_perm('inventory.change_stockmovement'):
    messages.success(request, 'Movement updated successfully!')
else:
    messages.warning(request, 'Changes saved as draft - approval required.')
```

## Configuration Options

### Toast Duration
Default: 5 seconds auto-hide
- Modify in base template if needed
- Set `data-bs-autohide="false"` to require manual close

### Position
Default: Top-right corner (`position-fixed top-0 end-0`)

### Z-Index
Default: 1080 (above modals: 1055, below tooltips: 1070)

## Do's and Don'ts

### ✅ Do's
- Use appropriate message types
- Keep messages concise and actionable
- Provide specific error context
- Use consistent language and tone

### ❌ Don'ts
- Don't create multiple toast containers
- Don't use toasts for critical errors that require immediate attention
- Don't make messages too long
- Don't forget to handle exceptions

## Testing

### Test Toast Functionality
```python
def test_success_message_displayed(self):
    response = self.client.post(self.url, self.valid_data)
    messages_list = list(messages.get_messages(response.wsgi_request))
    self.assertEqual(len(messages_list), 1)
    self.assertEqual(str(messages_list[0]), 'Expected message text')
    self.assertEqual(messages_list[0].tags, 'success')
```

## Debugging

### Check Messages in Template
```html
<!-- Debug: Show all messages -->
{% if messages %}
    <div class="debug-messages">
        {% for message in messages %}
            <p>{{ message.tags }}: {{ message }}</p>
        {% endfor %}
    </div>
{% endif %}
```

### Browser Console
Check for JavaScript errors if toasts don't appear:
```javascript
// Check if Bootstrap is loaded
console.log(typeof bootstrap);

// Check for toast elements
console.log(document.querySelectorAll('.toast').length);
```

---

*For complete documentation, see [toast-notification-system.md](./toast-notification-system.md)*
