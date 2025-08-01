# Stock Movement Edge Cases และการจัดการความเสี่ยง

## ภาพรวม

เอกสารนี้บอกรายละเอียดเกี่ยวกับปัญหา edge cases ที่อาจเกิดขึ้นในระบบ Stock Movement และวิธีการป้องกัน/แก้ไขที่ถูกออกแบบมาเพื่อรับมือกับสถานการณ์เหล่านี้

## ปัญหาหลักที่ระบุ

### 1. 🔌 **Power Failure during Stock Confirmation**
**สถานการณ์**: ระหว่างการ confirm stock movement เกิดไฟฟ้าดับหรือระบบขัดข้อง

**ผลกระทบ**:
- Stock Movement อาจค้างในสถานะ `PROCESSING`
- Stock records อาจถูกสร้างไม่สมบูรณ์
- ข้อมูลไม่สอดคล้องกันระหว่าง StockMovement และ Stock tables

### 2. 🏃‍♂️ **Concurrent Access**
**สถานการณ์**: หลาย user พยายาม confirm stock movement พร้อมกันสำหรับ item เดียวกัน

**ผลกระทบ**:
- Race condition ในการ allocate/deduct stock
- Over-allocation หรือ under-allocation

### 3. 💾 **Database Deadlock**
**สถานการณ์**: Database deadlock เกิดขึ้นระหว่างการประมวลผล stock

**ผลกระทบ**:
- Transaction failure
- Data inconsistency

### 4. 🔄 **Network Timeout**
**สถานการณ์**: Network connection timeout ระหว่างการประมวลผล

**ผลกระทบ**:
- Request ไม่สมบูรณ์
- User ไม่แน่ใจว่าการดำเนินการสำเร็จหรือไม่

## วิธีการป้องกัน (Prevention Mechanisms)

### 1. 🛡️ **Database Transactions**

```python
@transaction.atomic
def confirm(self, confirmed_by):
    """
    ใช้ atomic transaction เพื่อให้แน่ใจว่า:
    - ทุกการเปลี่ยนแปลงอยู่ใน transaction เดียว
    - หากมีข้อผิดพลาดเกิดขึ้น ทุกอย่างจะ rollback
    """
    try:
        self.status = self.Status.PROCESSING
        self.save()
        
        # Process all stock changes
        self._process_stock_changes(confirmed_by)
        
        self.status = self.Status.COMPLETED
        self.confirmed_at = timezone.now()
        self.confirmed_by = confirmed_by
        self.save()
        
    except Exception as e:
        self.status = self.Status.FAILED
        self.save()
        raise
```

**ประโยชน์**:
- หากเกิดปัญหาระหว่างทาง ข้อมูลจะถูก rollback กลับสู่สถานะเดิม
- ไม่มีข้อมูลแปลกๆ ค้างในระบบ

### 2. 🔒 **Pessimistic Locking**

```python
@classmethod
def allocate_stock_fefo(cls, item_sku, warehouse, required_quantity, user):
    """ใช้ select_for_update เพื่อป้องกัน concurrent access"""
    stock_records = cls.objects.select_for_update().filter(
        item_sku=item_sku,
        warehouse=warehouse,
        available_quantity__gt=0
    ).order_by('expiry_date', 'created_at')
```

**ประโยชน์**:
- ป้องกัน race condition
- แน่ใจว่ามีเพียง transaction เดียวที่แก้ไข stock record ได้ในแต่ละครั้ง

### 3. 📊 **Status Tracking**

```python
class Status(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    PROCESSING = 'PROCESSING', 'Processing Stock Changes'
    COMPLETED = 'COMPLETED', 'Stock Changes Completed'
    FAILED = 'FAILED', 'Stock Processing Failed'
```

**Flow การทำงาน**:
```
DRAFT → CONFIRMED → PROCESSING → COMPLETED/FAILED
```

**ประโยชน์**:
- ติดตามสถานะของ movement แต่ละตัว
- ระบุได้ว่า movement ไหนมีปัญหา
- สามารถ recover ได้

### 4. 🔧 **Version Control (Optimistic Locking)**

```python
class ValidatableMixin:
    version = models.PositiveIntegerField(default=1)
    
    def save(self, *args, **kwargs):
        if self.pk:
            # Check version before saving
            current_version = self.__class__.objects.get(pk=self.pk).version
            if current_version != self.version:
                raise ValidationError("Record has been modified by another user")
            self.version += 1
```

**ประโยชน์**:
- ป้องกันการ overwrite ข้อมูลโดยไม่รู้ตัว
- ตรวจจับ concurrent modifications

## วิธีการแก้ไข (Recovery Mechanisms)

### 1. 🔄 **Automatic Recovery in Model**

```python
def recover(self):
    """
    พยายามแก้ไข movement ที่มีปัญหาอัตโนมัติ
    """
    if self.status != self.Status.FAILED:
        raise ValidationError("Can only recover failed movements")
    
    try:
        with transaction.atomic():
            # Reset to CONFIRMED and try again
            self.status = self.Status.CONFIRMED
            self.save()
            
            # Try to confirm again
            if self.confirmed_by:
                self.confirm(self.confirmed_by)
            else:
                raise ValidationError("No confirmed_by user available for recovery")
                
    except Exception as e:
        self.status = self.Status.FAILED
        self.save()
        raise ValidationError(f"Recovery failed: {str(e)}")
```

### 2. 🛠️ **Recovery Management Command**

#### การใช้งาน:

```bash
# ดูรายการ movements ที่มีปัญหา (ไม่แก้ไข)
python manage.py recover_stock_movements --dry-run

# แก้ไข movement ทั้งหมดที่มีปัญหา
python manage.py recover_stock_movements

# แก้ไข movement เฉพาะ ID
python manage.py recover_stock_movements --movement-id 123

# แก้ไขเฉพาะ warehouse
python manage.py recover_stock_movements --warehouse-id 1
```

#### ฟีเจอร์:

- **Dry Run**: ดูปัญหาก่อนแก้ไข
- **Selective Recovery**: เลือกแก้ไขเฉพาะที่ต้องการ
- **Progress Reporting**: แสดงผลการดำเนินงาน
- **Error Handling**: จัดการ error และรายงาน

### 3. 🔍 **Consistency Check Command**

#### การใช้งาน:

```bash
# ตรวจสอบความสอดคล้องของข้อมูล
python manage.py check_stock_consistency

# ตรวจสอบและพยายามแก้ไข
python manage.py check_stock_consistency --fix

# ตรวจสอบเฉพาะ warehouse
python manage.py check_stock_consistency --warehouse-id 1
```

#### การตรวจสอบ:

1. **Orphaned Movements**: หา movements ที่ค้างใน `PROCESSING`/`FAILED`
2. **Balance Mismatches**: เปรียบเทียบ expected vs actual stock balances
3. **Data Integrity**: ตรวจสอบ referential integrity

## กรณีการใช้งานจริง (Real-world Scenarios)

### Scenario 1: ไฟฟ้าดับระหว่าง Confirm

**สถานการณ์**:
```
1. User กด confirm stock movement
2. ระบบเริ่ม process (status = PROCESSING)
3. ไฟฟ้าดับระหว่างการสร้าง stock records
4. ระบบ restart
```

**วิธีแก้ไข**:
```bash
# 1. ตรวจสอบสถานะ
python manage.py check_stock_consistency

# Output:
# ❌ Found 1 movements in inconsistent state
#    Movement 123: PROCESSING

# 2. กู้คืนข้อมูล
python manage.py recover_stock_movements --movement-id 123

# Output:
# ✅ Successfully recovered movement 123
```

### Scenario 2: Database Deadlock

**สถานการณ์**:
```
1. หลาย users confirm movements พร้อมกัน
2. Database deadlock เกิดขึ้น
3. บาง transactions fail (status = FAILED)
```

**วิธีแก้ไข**:
```bash
# กู้คืนทั้งหมดที่ failed
python manage.py recover_stock_movements

# ตรวจสอบความสอดคล้อง
python manage.py check_stock_consistency
```

### Scenario 3: Network Timeout

**สถานการณ์**:
```
1. User confirm แล้วไม่เห็น response
2. Movement อาจสำเร็จหรือไม่สำเร็จ
3. User ไม่แน่ใจสถานะ
```

**วิธีตรวจสอบ**:
```bash
# ตรวจสอบสถานะ movement
python manage.py check_stock_consistency --warehouse-id 1
```

## Best Practices สำหรับการป้องกัน

### 1. 📋 **Regular Monitoring**

```bash
# เพิ่มใน cron job เพื่อตรวจสอบทุกวัน
0 2 * * * cd /path/to/project && python manage.py check_stock_consistency
```

### 2. 🚨 **Alerting System**

```python
# ใน views หรือ signals
if movement.status == StockMovement.Status.FAILED:
    send_alert_to_admin(f"Stock movement {movement.id} failed")
```

### 3. 🔄 **Backup Strategy**

- **Database Backups**: สำรองข้อมูลก่อน migrations
- **Transaction Logs**: เก็บ logs สำหรับ forensic analysis
- **Recovery Testing**: ทดสอบ recovery procedures เป็นประจำ

### 4. 📊 **Performance Monitoring**

```sql
-- ตรวจสอบ slow queries
SELECT * FROM pg_stat_activity WHERE query LIKE '%stock%';

-- ตรวจสอบ deadlocks
SELECT * FROM pg_stat_database_conflicts;
```

## Database Schema Considerations

### 1. 📋 **Indexes สำหรับ Performance**

```python
class Meta:
    indexes = [
        # สำหรับ FEFO queries
        models.Index(fields=['item_sku', 'warehouse', 'expiry_date']),
        # สำหรับ FIFO queries  
        models.Index(fields=['item_sku', 'warehouse', 'lot_number']),
        # สำหรับ stock lookup
        models.Index(fields=['warehouse', 'item_sku']),
        # สำหรับ expiry monitoring
        models.Index(fields=['expiry_date']),
    ]
```

### 2. 🛡️ **Constraints สำหรับ Data Integrity**

```python
class Meta:
    constraints = [
        # Unique constraint
        models.UniqueConstraint(
            fields=('item_sku', 'warehouse', 'lot_number', 'expiry_date'),
            name='unique_stock_record'
        ),
        # Check constraint
        models.CheckConstraint(
            condition=models.Q(available_quantity__gte=0),
            name='positive_available_quantity'
        ),
    ]
```

## Troubleshooting Guide

### ปัญหาที่พบบ่อยและวิธีแก้ไข

#### 1. Movement ค้างใน PROCESSING

**อาการ**: Movement มี status = PROCESSING นานเกินไป

**วิธีแก้**:
```bash
python manage.py recover_stock_movements --movement-id [ID]
```

#### 2. Stock Balance ไม่ตรง

**อาการ**: ยอด stock ในระบบไม่ตรงกับ movements

**วิธีแก้**:
```bash
python manage.py check_stock_consistency --fix
```

#### 3. Performance ช้า

**อาการ**: การ confirm ใช้เวลานาน

**วิธีแก้**:
- ตรวจสอบ database indexes
- Optimize queries
- ใช้ connection pooling

#### 4. Deadlock บ่อย

**อาการ**: เกิด deadlock error บ่อย

**วิธีแก้**:
- ใช้ consistent ordering ในการ lock resources
- ลด transaction time
- ใช้ pessimistic locking ที่เหมาะสม

## Monitoring และ Alerting

### 1. 📊 **Key Metrics ที่ควรติดตาม**

- จำนวน movements ใน PROCESSING status
- จำนวน movements ใน FAILED status  
- Average confirmation time
- Deadlock frequency
- Balance discrepancies

### 2. 🚨 **Alert Conditions**

- Movement ค้างใน PROCESSING > 5 นาที
- มี FAILED movements เกิน 5% ของทั้งหมด
- Balance discrepancy > threshold
- Database deadlock > 10 ครั้ง/ชั่วโมง

### 3. 📈 **Dashboard Queries**

```sql
-- Movements by status
SELECT status, COUNT(*) FROM inventory_stockmovement 
GROUP BY status;

-- Average processing time
SELECT AVG(updated_at - confirmed_at) as avg_processing_time
FROM inventory_stockmovement 
WHERE status = 'COMPLETED';

-- Failed movements in last hour
SELECT COUNT(*) FROM inventory_stockmovement 
WHERE status = 'FAILED' 
AND updated_at > NOW() - INTERVAL '1 hour';
```

## สรุป

ระบบที่ออกแบบมาสามารถจัดการกับ edge cases ที่สำคัญได้:

✅ **Power failures** - Database transactions และ recovery commands
✅ **Concurrent access** - Pessimistic locking และ version control  
✅ **Data inconsistency** - Consistency checks และ automatic recovery
✅ **Performance issues** - Proper indexing และ monitoring
✅ **User experience** - Clear status tracking และ error messages

การใช้งานใน production ควรมี:
- Regular monitoring
- Automated recovery procedures  
- Proper alerting systems
- Performance optimization
- Regular backup และ testing procedures

---

**หมายเหตุ**: เอกสารนี้เป็นส่วนหนึ่งของ Stockflow Inventory Management System และควรถูก update เมื่อมีการเปลี่ยนแปลงในระบบ
