# Edge Cases และ Data Consistency Solutions

## ปัญหาที่เกิดขึ้น

### Scenario 1: ไฟฟ้าดับระหว่าง Confirm
```
1. User กด confirm StockMovement
2. StockMovement.status = CONFIRMED (บันทึกลง DB แล้ว)
3. 💥 ไฟฟ้าดับ ก่อนที่จะอัปเดต Stock records
4. ผลลัพธ์: StockMovement = CONFIRMED แต่ Stock ยังไม่ได้อัปเดต
```

### Scenario 2: Database Lock/Timeout
```
1. StockMovement confirmed
2. กำลังอัปเดต Stock record ที่ 1 สำเร็จ
3. 💥 Database timeout ขณะอัปเดต Stock record ที่ 2
4. ผลลัพธ์: Stock ไม่สอดคล้องกัน (partial update)
```

### Scenario 3: Concurrent Updates
```
1. User A confirm StockMovement (OUT 50 units)
2. User B confirm StockMovement (OUT 60 units) พร้อมกัน
3. ทั้งคู่เช็ค available stock = 100 units
4. ทั้งคู่คิดว่ามี stock เพียงพอ
5. ผลลัพธ์: Stock กลายเป็น -10 units
```

## วิธีแก้ไข

### 1. Database Transactions
### 2. Idempotent Operations  
### 3. Stock Reconciliation
### 4. Event Sourcing Pattern
### 5. Pessimistic Locking
