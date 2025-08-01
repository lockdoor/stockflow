# Stock Movement and Stock Integration Flow

```mermaid
flowchart TB
    subgraph USER_ACTIONS [User Actions]
        A[Create Stock Movement<br/>Status: DRAFT]
        B[Add Movement Items<br/>qty, lot, expiry]
        C[Confirm Movement<br/>Status: CONFIRMED]
    end
    
    subgraph SYSTEM_PROCESSING [System Processing]
        D{Movement<br/>Direction?}
        
        %% Stock IN Branch
        E[Stock IN Processing]
        F[For each Movement Item]
        G[Find/Create Stock Record<br/>item + warehouse + lot + expiry]
        H[Add Quantity to Stock]
        
        %% Stock OUT Branch  
        I[Stock OUT Processing]
        J[For each Movement Item]
        K[Check Available Stock<br/>in Warehouse]
        L{Sufficient<br/>Stock?}
        M[Apply FEFO Logic<br/>Order by expiry_date ASC]
        N[Allocate & Deduct<br/>from Stock Records]
        
        %% Error Handling
        O[Validation Error<br/>Insufficient Stock]
        P[Rollback Movement]
    end
    
    subgraph STOCK_OPERATIONS [Stock Table Operations]
        Q[(Stock Records)]
        R[Create New Stock Record<br/>available_quantity = qty]
        S[Update Existing Stock<br/>available_quantity += qty]
        T[Deduct from Stock<br/>available_quantity -= qty]
        U[Stock Record<br/>available_quantity = 0]
    end
    
    subgraph FEFO_DETAIL [FEFO Allocation Detail]
        V[Get Stock Records:<br/>item_sku + warehouse]
        W[Order by:<br/>1. expiry_date ASC<br/>2. lot_number ASC]
        X[Allocate from earliest<br/>expiring stock first]
        Y{More qty<br/>needed?}
        Z[Move to next<br/>stock record]
    end
    
    %% Main Flow
    A --> B
    B --> C
    C --> D
    
    %% Stock IN Flow
    D -->|IN| E
    E --> F
    F --> G
    G --> H
    H --> Q
    
    %% Stock OUT Flow
    D -->|OUT| I
    I --> J
    J --> K
    K --> L
    L -->|Yes| M
    L -->|No| O
    O --> P
    M --> N
    N --> Q
    
    %% Stock Operations
    G -.->|New Record| R
    G -.->|Existing Record| S
    H -.-> S
    N -.-> T
    T -.->|Qty becomes 0| U
    
    %% FEFO Detail
    M -.-> V
    V --> W
    W --> X
    X --> Y
    Y -->|Yes| Z
    Z --> X
    Y -->|No| N
    
    %% Styling
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style L fill:#fff3e0
    style O fill:#ffebee
    style Q fill:#e8f5e8
    style FEFO_DETAIL fill:#f3e5f5
    style STOCK_OPERATIONS fill:#e8f5e8
```

## Key Integration Points

### 1. Data Flow
```
StockMovement (Intent) → StockMovementItem (Details) → Stock (Actual Balance)
```

### 2. Relationship Mapping
- **One StockMovement** has **Many StockMovementItems**
- **One StockMovementItem** affects **One or More Stock Records** (for OUT movements)
- **One Stock Record** represents unique combination of: `item_sku + warehouse + lot_number + expiry_date`

### 3. FEFO Implementation
```python
# When processing Stock OUT movement item:
stock_records = Stock.objects.filter(
    item_sku=movement_item.item_sku,
    warehouse=movement.warehouse,
    available_quantity__gt=0
).order_by('expiry_date', 'lot_number')

# Allocate from earliest expiring stock first
remaining_qty = movement_item.quantity
for stock in stock_records:
    if remaining_qty <= 0:
        break
    
    allocated = min(stock.available_quantity, remaining_qty)
    stock.deduct_quantity(allocated)
    remaining_qty -= allocated
```

### 4. Stock Record States
```mermaid
stateDiagram-v2
    [*] --> Available: Stock IN
    Available --> Consumed: Stock OUT
    Available --> PartiallyConsumed: Stock OUT (partial)
    PartiallyConsumed --> Consumed: Stock OUT (remaining)
    PartiallyConsumed --> Available: Stock IN (replenish)
    Consumed --> Available: Stock IN (new stock)
    
    Available: available_quantity > 0
    PartiallyConsumed: 0 < available_quantity < original
    Consumed: available_quantity = 0
```
