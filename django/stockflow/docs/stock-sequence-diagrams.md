# Stock Management Sequence Diagrams

## Stock IN Sequence (Receiving Inventory)

```mermaid
sequenceDiagram
    participant User
    participant StockMovement
    participant StockMovementItem
    participant Stock
    participant System
    
    User->>StockMovement: Create movement (DRAFT)
    User->>StockMovementItem: Add items (qty, lot, expiry)
    User->>StockMovement: Confirm movement
    
    StockMovement->>System: Trigger confirm() method
    System->>StockMovement: Update status to CONFIRMED
    
    loop For each movement item
        System->>Stock: find_or_create_stock(item, warehouse, lot, expiry)
        alt Stock record exists
            Stock->>Stock: Add quantity to existing record
        else New stock record
            Stock->>Stock: Create new record with quantity
        end
        Stock->>System: Stock updated successfully
    end
    
    System->>User: Movement confirmed, stock updated
    
    Note over Stock: Stock balance increased<br/>Lot and expiry tracked
```

## Stock OUT Sequence (Consuming Inventory)

```mermaid
sequenceDiagram
    participant User
    participant StockMovement
    participant StockMovementItem
    participant Stock
    participant System
    
    User->>StockMovement: Create movement (DRAFT)
    User->>StockMovementItem: Add items (qty to consume)
    User->>StockMovement: Confirm movement
    
    StockMovement->>System: Trigger confirm() method
    
    loop For each movement item
        System->>Stock: get_stock_for_item(item, warehouse)
        Stock->>System: Return available stock records (FEFO order)
        
        alt Sufficient stock available
            System->>Stock: allocate_stock_fefo(item, warehouse, qty)
            
            loop For each stock record (FEFO order)
                Stock->>Stock: Calculate allocation amount
                Stock->>Stock: deduct_quantity(allocated_amount)
                alt Stock record depleted
                    Note over Stock: available_quantity = 0
                else Stock record partial
                    Note over Stock: available_quantity reduced
                end
            end
            
            Stock->>System: Allocation successful
        else Insufficient stock
            System->>User: Error: Insufficient stock
            System->>StockMovement: Rollback to DRAFT
        end
    end
    
    alt All items processed successfully
        System->>StockMovement: Update status to CONFIRMED
        System->>User: Movement confirmed, stock consumed
    else Any item failed
        System->>StockMovement: Keep as DRAFT
        System->>User: Movement failed, fix issues
    end
    
    Note over Stock: Stock balance decreased<br/>FEFO allocation applied
```

## FEFO Allocation Detail

```mermaid
sequenceDiagram
    participant System
    participant Stock as Stock Records
    
    System->>Stock: Need 100 units of Item A
    Stock->>System: Available records:<br/>Lot001 (50 units, exp: 2025-08-01)<br/>Lot002 (80 units, exp: 2025-08-15)<br/>Lot003 (30 units, exp: 2025-09-01)
    
    Note over System,Stock: Apply FEFO Logic
    
    System->>Stock: Allocate from Lot001 (earliest expiry)
    Stock->>System: Take 50 units (fully depletes Lot001)
    
    System->>Stock: Still need 50 units, allocate from Lot002
    Stock->>System: Take 50 units (Lot002 has 30 remaining)
    
    System->>Stock: Allocation complete (100 units total)
    
    Note over Stock: Final state:<br/>Lot001: 0 units<br/>Lot002: 30 units<br/>Lot003: 30 units (untouched)
```

## Error Handling Sequence

```mermaid
sequenceDiagram
    participant User
    participant System
    participant StockMovement
    participant Stock
    
    User->>StockMovement: Confirm movement (OUT)
    StockMovement->>System: Process confirmation
    
    System->>Stock: Check available stock
    Stock->>System: Available: 50 units
    
    alt Requested quantity > Available
        System->>System: Validation Error
        System->>StockMovement: Keep status as DRAFT
        System->>User: Error: Insufficient stock (need 100, have 50)
        
        Note over User: User must either:<br/>1. Reduce quantity<br/>2. Add more stock<br/>3. Cancel movement
        
    else Sufficient stock
        System->>Stock: Proceed with allocation
        Stock->>System: Success
        System->>StockMovement: Update to CONFIRMED
        System->>User: Movement confirmed
    end
```

## Stock Record Lifecycle

```mermaid
sequenceDiagram
    participant Movement as Stock Movement
    participant Stock as Stock Record
    participant System
    
    Note over Stock: Initial State: Does not exist
    
    Movement->>System: Stock IN confirmed (Lot A, 100 units)
    System->>Stock: Create new record
    Stock->>Stock: available_quantity = 100
    
    Note over Stock: State: Available (100 units)
    
    Movement->>System: Stock OUT confirmed (50 units)
    System->>Stock: Apply FEFO allocation
    Stock->>Stock: available_quantity = 50
    
    Note over Stock: State: Partially Consumed (50 units)
    
    Movement->>System: Stock OUT confirmed (50 units)
    System->>Stock: Apply FEFO allocation
    Stock->>Stock: available_quantity = 0
    
    Note over Stock: State: Consumed (0 units)
    
    Movement->>System: Stock IN confirmed (200 units, same lot)
    System->>Stock: Add to existing record
    Stock->>Stock: available_quantity = 200
    
    Note over Stock: State: Available (200 units)
```
