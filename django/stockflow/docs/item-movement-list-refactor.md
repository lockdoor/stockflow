# Refactored Item Movement List

## เปรียบเทียบการ Refactor

### Before (เดิม)
```html
<div id="item-movement-list">
    <div class="overflow-x-auto">
        <table class="table table-zebra table-pin-rows">
            <!-- Table content -->
        </table>
    </div>
</div>
```

### After (ใหม่)
```html
{% if movement_items is not None %}
{# Case 1: มี context - render table โดยตรง #}
<div class="flex items-center justify-center">
    <div class="bg-white p-8 m-4 rounded shadow-md w-full">
        <!-- Full table with controls -->
    </div>
</div>
{% else %}
{# Case 2: ไม่มี context - ใช้ HTMX fetch #}
<div id="item-movement-list-htmx" 
    hx-get="{% url 'inventory:stock-item-movement-list' stock_movement.id %}" 
    hx-trigger="load">
    <!-- Loading state -->
</div>
{% endif %}
```

## การเปลี่ยนแปลงหลัก

### 1. **Conditional Rendering**
- รองรับทั้งการส่ง context และ HTMX fetch
- ใช้ `movement_items is not None` เหมือน bom-list

### 2. **Layout Consistency**
- เพิ่ม wrapper และ styling เดียวกับ bom-list
- Title และ button positioning

### 3. **HTMX Integration**
- Loading state พร้อม spinner
- Auto-fetch เมื่อไม่มี context

### 4. **Button Actions**
- Add New Movement button
- Modal integration

### 5. **Error Handling**
- Better colspan (10 แทน 5)
- Consistent error messaging

## ไฟล์ที่เกี่ยวข้องที่สร้าง/แก้ไข

1. **item-movement-list.html** - Template หลัก
2. **item-movement-row.html** - แก้ไข field mapping
3. **item-movement-form.html** - Form ใหม่ที่ใช้ autocomplete
4. **URLs** - ปรับ URL mapping ให้ถูกต้อง

## ประโยชน์

1. **Consistency** - รูปแบบเดียวกับ bom-list
2. **Flexibility** - รองรับหลาย use case
3. **Performance** - HTMX lazy loading
4. **Reusability** - ใช้ autocomplete component ร่วม
5. **Maintainability** - Structure ที่ชัดเจน

## การใช้งาน

### แบบส่ง Context
```django
{% include 'inventory/item/partials/item-movement-list.html' with movement_items=items stock_movement=movement warehouse=warehouse %}
```

### แบบ HTMX Auto-fetch
```django
{% include 'inventory/item/partials/item-movement-list.html' with stock_movement=movement warehouse=warehouse %}
```
