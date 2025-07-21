# Item Autocomplete Form Interface

## Overview
The `item-autocomplete-form.html` is a reusable partial template that provides item selection functionality with autocomplete search for various forms across the application.

## Features
- Dynamic item search with HTMX
- Category-based filtering
- Flexible field mapping (component_sku, item_sku, etc.)
- Customizable labels and button text
- Support for both create and update operations

## Required Context Variables

### Mandatory
- `form`: Form instance containing the item selection field
- `create_url`: URL name for create operation
- `create_target`: Target element prefix for HTMX response on create
- `update_url`: URL name for update operation
- `update_target`: Target element prefix for HTMX response on update

### Optional
- `autocomplete_url`: URL name for autocomplete endpoint (default: 'catalog:item-bom-autocomplete')
- `field_label`: Label for the search field (default: 'Component')
- `submit_text_create`: Text for create button (default: 'Add Component')
- `submit_text_update`: Text for update button (default: 'Edit Component')
- `parent_sku`: Parent object for create operations
- `category`: List of categories for filtering

## Form Requirements

The form must have at least one of these fields:
- `component_sku` (for BOM components)
- `item_sku` (for inventory items)
- Any field ending with `_sku` and having `type="hidden"`

If applicable, the form should also have:
- `quantity` field for quantity input

## Usage Examples

### BOM Form
```django
{% include 'catalog/item/partials/item-autocomplete-form.html' with 
    create_url='catalog:bom-create' 
    update_url='catalog:bom-edit' 
    form=bom_form 
    create_target='bom' 
    update_target='bom' 
    autocomplete_url='catalog:item-bom-autocomplete' 
    field_label='Component' 
    submit_text_create='Add Component' 
    submit_text_update='Edit Component' %}
```

### Stock Movement Form
```django
{% include 'catalog/item/partials/item-autocomplete-form.html' with 
    create_url='inventory:stock-create' 
    form=stock_form 
    create_target='stock' 
    autocomplete_url='catalog:item-autocomplete' 
    field_label='Item' 
    submit_text_create='Add Stock Movement' %}
```

### Purchase Order Line Form
```django
{% include 'catalog/item/partials/item-autocomplete-form.html' with 
    create_url='purchasing:po-line-create' 
    form=po_line_form 
    create_target='po-line' 
    field_label='Product' 
    submit_text_create='Add Line Item' %}
```

## JavaScript Behavior

The template includes JavaScript that:
1. Handles autocomplete result selection
2. Automatically finds the appropriate hidden SKU field
3. Clears results when clicking outside
4. Updates both display and hidden field values

## Supported Field Types

The JavaScript automatically detects and works with:
- `id_component_sku`
- `id_item_sku`
- Any input with `name*="sku"` and `type="hidden"`

## Backend Requirements

### Autocomplete View
Create a view that returns filtered items:
```python
class ItemAutocompleteView(LoginRequiredMixin, ListView):
    model = ItemSKU
    template_name = "catalog/item/partials/autocomplete-results.html"
    
    def get_queryset(self):
        query = self.request.GET.get("q", "")
        category_id = self.request.GET.get("category")
        # ... filtering logic
```

### URL Configuration
```python
path("items/autocomplete/", ItemAutocompleteView.as_view(), name="item-autocomplete"),
```

## Migration Guide

### From Specific Form to Generic Interface

1. **Replace direct template inclusion:**
   ```django
   <!-- Before -->
   {% include 'catalog/bom/partials/bom-form.html' %}
   
   <!-- After -->
   {% include 'catalog/item/partials/item-autocomplete-form.html' with ... %}
   ```

2. **Update context variables:**
   - Map existing URLs to new parameter names
   - Provide field labels and button text
   - Ensure form has correct field names

3. **Test functionality:**
   - Verify autocomplete works
   - Check form submission
   - Confirm HTMX responses

## Benefits

1. **Code Reuse**: Single template for all item selection forms
2. **Consistency**: Uniform behavior across the application
3. **Maintainability**: Changes in one place affect all forms
4. **Flexibility**: Easy customization through parameters
5. **Testing**: Single component to test thoroughly
