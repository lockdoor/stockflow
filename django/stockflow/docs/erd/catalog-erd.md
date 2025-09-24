# Catalog Context - Entity Relationship Diagram


```mermaid
erDiagram
    %% Catalog Context - StockFlow System
    
    Category {
        int id PK
        varchar name UK "Unique category name"
        text note "Optional description"
        bool is_active "Status flag"
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version "For optimistic locking"
    }
    Category }o--|| User : "created_by"
    Category }o--|| User : "updated_by"

    ItemSKU {
        int id PK
        varchar sku_code UK "Unique SKU identifier"
        varchar name "Item display name"
        varchar unit "Unit of measurement"
        enum type "RAW, PRODUCT"
        enum status "ACTIVE, INACTIVE, DRAFT"
        text note "Additional notes"
        int category_id FK "Optional category"
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version "For optimistic locking"
    }
    ItemSKU }o--o| Category : "category_id"
    ItemSKU }o--|| User : "created_by"
    ItemSKU }o--|| User : "updated_by"

    BOM {
        int id PK
        int parent_sku_id FK "Item that contains components"
        int component_sku_id FK "Component item"
        decimal quantity "Required quantity"
        varchar note "Additional notes"
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
        int version "For optimistic locking"
    }
    BOM }o--|| ItemSKU : "parent_sku_id"
    BOM }o--|| ItemSKU : "component_sku_id"
    BOM }o--|| User : "created_by"
    BOM }o--|| User : "updated_by"

    ItemImage {
        int id PK
        int item_id FK "Related item"
        varchar image "Image file path"
        varchar caption "Optional image caption"
        bool is_primary "Primary image flag"
        timestamp created_at
        int created_by FK
        timestamp updated_at
        int updated_by FK
    }
    ItemImage }o--|| ItemSKU : "item_id"
    ItemImage }o--|| User : "created_by"
    ItemImage }o--|| User : "updated_by"

    %% External Context Entity
    User {
        int id PK
        varchar username
        varchar email
        varchar first_name
        varchar last_name
    }

    %% Relationships Summary:
    %% 1. Category (1) -> (0..N) ItemSKU (Optional relationship)
    %% 2. ItemSKU (1) -> (0..N) BOM as parent (PRODUCT/PACKAGE can have BOM)
    %% 3. ItemSKU (1) -> (0..N) BOM as component (All items can be components)
    %% 4. ItemSKU (1) -> (0..N) ItemImage (Items can have multiple images)
    %% 5. User (1) -> (0..N) All entities (Audit trail)

    %% Business Rules:
    %% - Only PRODUCT and PACKAGE type items can have BOM as parent
    %% - All item types can be used as components in BOM
    %% - SKU codes must be unique across the system
    %% - Category names must be unique
    %% - BOM cannot have circular references (A -> B -> A)
    %% - One primary image per item
```


## Key Relationships and Business Rules

### **Category -> ItemSKU**
- **Relationship**: One-to-Many (Optional)
- **Business Rule**: Items can optionally belong to a category
- **Notes**: Category can be null, allowing items without categorization

### **ItemSKU -> BOM (as Parent)**
- **Relationship**: One-to-Many
- **Business Rule**: Only PRODUCT and PACKAGE type items can have BOM
- **Notes**: RAW materials cannot have sub-components

### **ItemSKU -> BOM (as Component)**
- **Relationship**: One-to-Many
- **Business Rule**: All item types can be used as components
- **Notes**: Enables flexible BOM structures

### **ItemSKU -> ItemImage**
- **Relationship**: One-to-Many
- **Business Rule**: Items can have multiple images with one primary
- **Notes**: Primary image used for display purposes

### **Audit Trail**
- **All entities include**: created_by, created_at, updated_by, updated_at
- **Optimistic Locking**: version field for concurrent update protection
- **User Tracking**: Full audit trail of who created/modified records

## Entity Constraints

### **ItemSKU**
- `sku_code`: Unique, required
- `type`: Cannot be changed once set
- `status`: Controls item visibility and usage

### **Category**
- `name`: Unique, required
- `is_active`: Controls category availability

### **BOM**
- Unique constraint on (parent_sku_id, component_sku_id)
- Circular reference prevention
- Quantity must be positive

### **ItemImage**
- Only one primary image per item
- Image file validation for supported formats

## Database Indexes

### **Performance Indexes**
- ItemSKU: sku_code, type, status, created_at
- Category: name, is_active
- BOM: parent_sku_id, component_sku_id
- ItemImage: item_id, is_primary

This ERD represents the complete catalog context with proper relationships, constraints, and business rules for the StockFlow inventory management system.
