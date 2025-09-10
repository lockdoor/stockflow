# Production Process Action Card Improvements

## Overview
ปรับปรุง Production Process Unified Form ให้มี Action Card ที่แยกออกมาสำหรับการจัดการ workflow ต่างๆ ได้อย่างชัดเจน

## Changes Made

### 1. View Improvements (`production/views/production_process_unified.py`)

#### Added RedirectMixin Integration
```python
from common.mixins.redirect import RedirectMixin

class ProductionProcessUnifiedView(ProductionPermissionMixin, RedirectMixin, View):
```

#### Enhanced Action Handling
- **Save Draft**: บันทึกและ redirect กลับไป order detail
- **Update Draft**: บันทึกและอยู่หน้าเดิม  
- **Confirm**: ยืนยันและ redirect กลับไป order detail

#### New Methods Added
- `_handle_action_redirect()`: จัดการ redirect ตาม action
- `_handle_confirmation()`: ปรับปรุงให้รองรับ AJAX และ redirect ที่ถูกต้อง
- `get_default_success_url()` / `get_default_prev_url()`: ใช้ RedirectMixin

### 2. Template Improvements (`production-process-unified-form.html`)

#### Action Card Design
```html
<!-- Action Card -->
<div class="col-lg-8">
    <div class="card shadow-sm mt-3">
        <div class="card-header">
            <h5 class="card-title mb-0">
                <i class="bi bi-lightning me-1"></i>Actions
            </h5>
        </div>
        <div class="card-body">
            <div class="row g-3">
                <!-- Save Draft Action -->
                <div class="col-md-4">
                    <button type="button" class="btn btn-outline-primary btn-lg action-btn" 
                            data-action="save_draft">
                        <div class="text-center">
                            <i class="bi bi-file-earmark-text fs-4 d-block mb-2"></i>
                            <strong>Save Draft</strong>
                            <small class="d-block text-muted">Save and return to order</small>
                        </div>
                    </button>
                </div>
                
                <!-- Update Draft Action -->
                <div class="col-md-4">
                    <button type="button" class="btn btn-outline-info btn-lg action-btn" 
                            data-action="update_draft">
                        <div class="text-center">
                            <i class="bi bi-pencil-square fs-4 d-block mb-2"></i>
                            <strong>Update Draft</strong>
                            <small class="d-block text-muted">Save and stay here</small>
                        </div>
                    </button>
                </div>
                
                <!-- Confirm Process Action -->
                <div class="col-md-4">
                    <button type="button" class="btn btn-success btn-lg action-btn" 
                            data-action="confirm">
                        <div class="text-center">
                            <i class="bi bi-check-circle fs-4 d-block mb-2"></i>
                            <strong>Confirm Process</strong>
                            <small class="d-block text-muted">Apply to stock</small>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### Enhanced JavaScript
- Form validation ก่อน submit
- AJAX handling สำหรับ better UX
- Error handling และแสดง loading states
- Dynamic redirect behavior ตาม action

### 3. User Experience Improvements

#### Clear Action Flow
1. **Save Draft**: บันทึกข้อมูลและกลับไปดู Production Order
2. **Update Draft**: บันทึกและยังคงอยู่หน้าเดิมเพื่อแก้ไขต่อ
3. **Confirm**: ยืนยัน production process และ apply stock movements

#### Visual Design
- Action buttons ที่มี icon และคำอธิบายชัดเจน
- Color coding: Primary (Save), Info (Update), Success (Confirm)
- Large buttons เพื่อความสะดวกในการใช้งาน

#### Form Validation
- ตรวจสอบ required fields
- ตรวจสอบว่ามี finished products อย่างน้อย 1 รายการ
- แสดง error messages ที่เข้าใจง่าย

### 4. Technical Benefits

#### Consistent Redirect Behavior
- ใช้ `RedirectMixin` จาก `common.mixins.redirect`
- รองรับ `next` และ `prev` parameters
- Fallback URLs ที่เหมาะสม

#### AJAX Support
- รองรับ XMLHttpRequest สำหรับ modern UI
- JSON response สำหรับ error handling
- Better user experience โดยไม่ต้อง reload หน้า

#### Error Handling
- Proper validation error messages
- Transaction rollback on errors
- User-friendly error displays

## Usage Examples

### Creating New Production Process
1. Fill in process name and notes
2. Add finished products (required)
3. Add material losses (optional)
4. Click **Save Draft** to save and return to order

### Editing Draft Process
1. Make changes to process details
2. Click **Update Draft** to save changes and continue editing
3. Or click **Save Draft** to save and return to order
4. When ready, click **Confirm** to finalize

### Confirming Process
1. Ensure all data is correct
2. Click **Confirm Process**
3. System validates WIP balance
4. Applies stock movements
5. Returns to Production Order with success message

## Files Modified
- `production/views/production_process_unified.py`
- `production/templates/production/production-process/production-process-unified-form.html`

## Dependencies
- `common.mixins.redirect.RedirectMixin` - สำหรับจัดการ redirect logic
- Bootstrap 5 - สำหรับ UI components
- Django Forms & Formsets - สำหรับ form handling

## Testing
- Server starts successfully without errors
- All form fields render correctly
- Action buttons are properly styled and positioned
- JavaScript handlers are attached to buttons
- AJAX and regular form submissions both supported

## Next Steps
1. Test the actual form submission and redirect behavior
2. Verify WIP balance validation works correctly
3. Test error handling scenarios
4. Ensure all responsive design works on mobile devices
