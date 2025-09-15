# Production Order Completion Enhancement

## Overview

เพิ่มฟีเจอร์การตรวจสอบความสมบูรณ์ของการผลิตใน COMPLETED status โดยตรวจสอบว่า actual quantity มากกว่าหรือเท่ากับ planned quantity หากเป็นจริงจะแสดงปุ่ม "Complete Order" แทน "Cancel Order"

## Changes Made

### 1. Model Enhancements (`production/models/production_order.py`)

เพิ่ม methods ใหม่:
- `is_production_complete()`: ตรวจสอบว่า actual quantity ≥ planned quantity สำหรับทุก BOM items
- `can_complete_production()`: ตรวจสอบว่าสามารถทำการ complete production order ได้หรือไม่

```python
def is_production_complete(self):
    """Check if actual production quantity meets or exceeds planned quantity for all BOM items"""
    bom_items = self.boms.all()
    if not bom_items.exists():
        return False
        
    for bom in bom_items:
        if bom.actual_quantity < bom.planned_quantity:
            return False
    return True

def can_complete_production(self):
    """Check if this production order can be completed"""
    return (
        self.status == self.Status.COMPLETED and 
        self.is_production_complete()
    )
```

### 2. New Views (`production/views/production_order_status_views.py`)

เพิ่ม views ใหม่:
- `ProductionOrderCompleteConfirmView`: แสดงหน้า confirm การ complete
- `ProductionOrderCompleteView`: จัดการ logic การ complete และคืน WIP materials

### 3. New Template (`production/templates/production/orders/production-order-complete-confirm.html`)

สร้างหน้า confirmation สำหรับการ complete production order ที่:
- แสดงสรุปข้อมูล production order
- แสดงสถานะการผลิต (complete/partial)
- แสดง WIP materials ที่จะถูกคืน
- ให้ใส่ notes การ complete
- มี checkbox confirmation

### 4. Template Updates (`production/templates/production/orders/production-order-detail.html`)

แก้ไข COMPLETED status actions:
- เพิ่ม progress bar แสดง actual vs planned quantity
- เพิ่มการแสดงสถานะ "Target Met" หรือ "Partial" 
- เปลี่ยนปุ่มจาก "Cancel Order" เป็น "Complete Order" เมื่อ `is_production_complete()` เป็น true

### 5. URL Patterns (`production/urls.py`)

เพิ่ม URL patterns ใหม่:
```python
path('production-order/<int:pk>/complete/confirm/', ProductionOrderCompleteConfirmView.as_view(), name='production-order-complete-confirm'),
path('production-order/<int:pk>/complete/', ProductionOrderCompleteView.as_view(), name='production-order-complete'),
```

## User Flow

### การ Complete Production Order

1. ผู้ใช้เข้าดู production order ที่มีสถานะ COMPLETED
2. ระบบตรวจสอบ actual vs planned quantity:
   - หาก actual ≥ planned ทุกรายการ: แสดงปุ่ม "Complete Order" (สีเขียว)
   - หาก actual < planned บางรายการ: แสดงปุ่ม "Cancel Order" (สีแดง)
3. เมื่อคลิก "Complete Order":
   - ไปหน้า confirmation แสดงสรุปข้อมูล
   - แสดงสถานะการผลิตและ WIP materials ที่จะคืน
   - ให้ใส่ completion notes (optional)
   - ต้อง check confirmation checkbox
4. เมื่อ confirm:
   - คืน WIP materials กลับ stock (ถ้ามี)
   - Release material reservations
   - Close production order as completed
   - บันทึก completion notes

## Business Logic

### การตรวจสอบความสมบูรณ์
- ใช้ `actual_quantity` จาก ProductionOrderBOM model
- `actual_quantity` คำนวณจาก ProductionResult ที่มีสถานะ CONFIRMED
- ต้องผ่าน target ทุกรายการใน BOM

### การคืน WIP Materials
- เหมือนกับ flow การ cancel
- สร้าง stock movement แบบ IN เพื่อคืน materials
- สร้าง WIP stock movement เพื่อลด WIP balance
- Auto confirm stock movement

### การจัดการ Reservations
- Release material reservations ที่เหลือ
- Log การ operation สำหรับ audit trail

## Testing

ทดสอบผ่าน Django checks:
```bash
python manage.py check
# System check identified no issues (0 silenced)
```

## Benefits

1. **User Experience**: ชัดเจนว่าเมื่อไหร่ควร complete หรือ cancel
2. **Data Integrity**: ตรวจสอบความสมบูรณ์ของการผลิตก่อน complete
3. **Visual Feedback**: Progress bars แสดงสถานะการผลิต
4. **Audit Trail**: บันทึก completion notes และ stock movements
5. **Consistency**: ใช้ flow เดียวกับ cancel (WIP return, reservation release)

## Technical Notes

- ใช้ `@transaction.atomic` เพื่อความปลอดภัยของข้อมูล
- สร้าง unique lot numbers สำหรับ WIP returns
- Error handling และ user feedback ครบถ้วน
- Compatible กับ existing permission system
- ไม่กระทบ existing functionality
