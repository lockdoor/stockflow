conda

```
conda env list
```

check env stockflow is existed

if not create env stockflow
```
conda create --name stockflow
```

activate
```
conda activate stockflow
```

install package requirement
```
pip install -r requirements.txt
```

run server
```
python3 manage.py runserver 0.0.0.0:8000
```

separation of concerns:

**Form Layer:**
- Form validation (required fields, input format)
- User input validation
- UI/UX validation

**Model Layer:**
- Business logic validation
- Data integrity rules
- Domain-specific validation 

## ✅ **การแบ่งหน้าที่ใหม่:**

### **📝 Form Layer (ValidationError)**
- **Required validation** - ตรวจสอบ field ที่จำเป็น
- **Input format validation** - ตรวจสอบรูปแบบ input
- **Basic cleaning** - strip whitespace, normalize data
- **UI/UX validation** - validation ที่เกี่ยวกับ user experience

### **🔧 Model Layer (ValueError)**
- **Business logic validation** - duplicate name, business rules
- **Data integrity validation** - ข้อมูลที่ถูกต้องตาม business domain
- **Optimistic locking** - concurrency control
- **Domain-specific rules** - กฎเฉพาะของ business

## 🎯 **ข้อดีของการแบ่งแบบนี้:**

### **1. Clear Separation of Concerns**
- Form รับผิดชอบ input validation
- Model รับผิดชอบ business logic

### **2. Better Error Handling**
- `ValidationError` → Form/UI errors
- `ValueError` → Business logic errors

### **3. Maintainability**
- Form validation ไม่ต้อง query database
- Model validation ครอบคลุม business rules

### **4. Reusability**
- Business logic validation ใช้ได้กับทุก interface (API, admin, etc.)
- Form validation ใช้ได้กับ web forms

## 🔄 **Flow การทำงาน:**
1. **Form validation** → ตรวจสอบ required, format, cleaning
2. **Model validation** → ตรวจสอบ business logic เมื่อ save()
3. **Error conversion** → แปลง ValueError เป็น ValidationError ใน form.save()

**ผลลัพธ์:** Form สะอาด เน้นแค่ input validation, Model จัดการ business logic เต็มที่!