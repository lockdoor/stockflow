---
title: Production Context ERD
created: 2025-08-19
---

# Production Context ERD


```mermaid
erDiagram
    %% Production Context - StockFlow System
    ProductionOrder {
        int id PK
        string status "Draft, Created, In Progress, Completed, Cancelled"
        int warehouse_id FK
        text note "Optional notes"
        timestamp started_at
        timestamp finished_at
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version "For optimistic locking"
    }
    ProductionOrderBOM {
        int id PK
        int production_order_id FK
        int item_sku_id FK "ผลิตสินค้าชนิดนี้ตาม BOM นี้"
        decimal planned_quantity
        text note
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version
    }
    StockMovement_Inventory {
        int id PK
        enum reference_type "NONE, ADJUST, PACKING_LIST, PRODUCTION, INVOICE"
        int reference_id "FK to ProductionOrder when reference_type=PRODUCTION"
        text note
        int warehouse_id FK
        enum status "DRAFT, CONFIRMED"
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version
    }
    StockMovementItem_Inventory {
        int id PK
        int stock_movement_id FK
        int item_sku_id FK
        enum movement_type "IN, OUT"
        decimal quantity
        varchar lot_number
        date expiry_date
        text note
        int created_by FK
        int updated_by FK
        timestamp created_at
        timestamp updated_at
        int version
    }
    ProductionProcess {
        int id PK
        int production_order_id FK
        datetime started_at
        datetime finished_at
        text note
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version
    }
    ProductionResult {
        int id PK
        int production_process_id FK
        int item_sku_id FK
        decimal quantity
        text note
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version
    }
    ProductionLoss {
        int id PK
        int production_process_id FK
        int item_sku_id FK
        decimal quantity
        string reason
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version
    }
    ItemSKU_Catalog {
        int id PK
        string sku_code UK
        string name
    }
    Warehouse_Inventory {
        int id PK
        string code UK
        string name
    }
    User_User {
        int id PK
        string username
    }

    ProductionOrder ||--o{ StockMovement_Inventory : "material movements"
    StockMovement_Inventory }o--|| ProductionOrder : "reference_id (if PRODUCTION)"
    StockMovement_Inventory ||--o{ StockMovementItem_Inventory : "has items"
    StockMovementItem_Inventory }o--|| ItemSKU_Catalog : "item_sku_id"
    StockMovementItem_Inventory }o--|| Warehouse_Inventory : "warehouse_id"
    ProductionOrder ||--o{ ProductionProcess : "has"
    ProductionProcess ||--o{ ProductionResult : "has results"
    ProductionProcess ||--o{ ProductionLoss : "has losses"
    ProductionOrder ||--o{ ProductionOrderBOM : "has BOMs"
    ProductionOrderBOM }o--|| ItemSKU_Catalog : "item_sku_id"
    ProductionOrder }o--|| User_User : "created_by"

    ProductionProcess }o--|| User_User : "created_by"
    ProductionProcess }o--|| ProductionResult : "yields"
    ProductionProcess }o--|| ProductionLoss : "causes"
    ProductionResult }o--|| ItemSKU_Catalog : "item_sku_id"
    ProductionResult }o--|| User_User : "created_by"
    ProductionLoss }o--|| ItemSKU_Catalog : "item_sku_id"
    ProductionLoss }o--|| User_User : "created_by"
```

## Key Relationships and Business Rules

### **ProductionOrder -> ProductionMaterialWithdraw / ProductionProcess / ProductionResult / ProductionLoss**
- **Relationship**: One-to-Many
- **Business Rule**: ทุกกิจกรรมต้องอ้างอิง ProductionOrder เสมอ
- **Notes**: ใช้สำหรับ track กระบวนการผลิตและผลลัพธ์

### **ProductionOrder -> BOM**
- **Relationship**: Many-to-One
- **Business Rule**: ต้องเลือก BOM ที่ใช้ในการผลิตแต่ละ order

### **ProductionMaterialWithdraw -> ItemSKU / Warehouse**
- **Relationship**: Many-to-One
- **Business Rule**: การเบิกวัสดุต้องระบุ item และ warehouse
- **Notes**: รองรับ partial withdraw

### **ProductionResult -> ItemSKU / Warehouse**
- **Relationship**: Many-to-One
- **Business Rule**: ผลิตภัณฑ์ที่ผลิตเสร็จต้องระบุ item และ warehouse ที่จัดเก็บ

### **ProductionLoss -> ItemSKU**
- **Relationship**: Many-to-One
- **Business Rule**: ต้องบันทึกเหตุผลและปริมาณวัสดุที่สูญเสีย

### **Audit Trail**
- **All entities include**: created_by, created_at, version
- **Optimistic Locking**: version field for concurrent update protection
- **User Tracking**: Full audit trail of who created/modified records

## Entity Constraints

### **ProductionOrder**
- `status`: Enum, only allowed values
- `version`: Optimistic locking

### **ProductionMaterialWithdraw / ProductionResult / ProductionLoss**
- `quantity`: Must be positive
- `item_sku_id`, `warehouse_id`: FK, required

### **ProductionProcess**
- `process_date`: Required

### **BOM**
- ต้องมีความสัมพันธ์กับ ProductionOrder

## Database Indexes

### **Performance Indexes**
- ProductionOrder: status, created_at
- ProductionMaterialWithdraw: production_order_id, item_sku_id, warehouse_id
- ProductionResult: production_order_id, item_sku_id, warehouse_id
- ProductionLoss: production_order_id, item_sku_id

---
โครงสร้างนี้แสดงความสัมพันธ์, constraints, business rules และ audit trail สำหรับ Production Context ในระบบ StockFlow
