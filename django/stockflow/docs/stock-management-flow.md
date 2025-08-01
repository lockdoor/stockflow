# Stock Management Flow

## Overview
This document describes the flow of stock management in the StockFlow system, showing how StockMovement and Stock models interact during inventory operations.

## Stock Management Flowchart

```mermaid
flowchart TD
    A[Create Stock Movement] --> B{Movement Type?}
    
    %% Stock IN Flow
    B -->|Stock IN| C[Add Stock Movement Items]
    C --> D[User Confirms Movement]
    D --> E[Stock Movement Status = CONFIRMED]
    E --> F[Process Stock IN Items]
    
    F --> G[For Each Movement Item]
    G --> H[Find or Create Stock Record]
    H --> I{Stock Record Exists?}
    I -->|Yes| J[Add Quantity to Existing Stock]
    I -->|No| K[Create New Stock Record]
    K --> L[Set Initial Quantity]
    J --> M[Update Stock Balance]
    L --> M
    
    %% Stock OUT Flow  
    B -->|Stock OUT| N[Add Stock Movement Items]
    N --> O[User Confirms Movement]
    O --> P[Stock Movement Status = CONFIRMED]
    P --> Q[Process Stock OUT Items]
    
    Q --> R[For Each Movement Item]
    R --> S[Check Available Stock]
    S --> T{Sufficient Stock?}
    T -->|No| U[Validation Error]
    T -->|Yes| V[Allocate Stock using FEFO/FIFO]
    
    V --> W[Get Stock Records Ordered by Expiry Date]
    W --> X[For Each Stock Record]
    X --> Y{Remaining Qty > 0?}
    Y -->|No| Z[Allocation Complete]
    Y -->|Yes| AA[Calculate Allocation Amount]
    AA --> BB[Deduct from Stock Record]
    BB --> CC{More Stock Records?}
    CC -->|Yes| X
    CC -->|No| Z
    
    %% Final Steps
    M --> DD[Stock Balance Updated]
    Z --> EE[Stock Balance Updated]
    DD --> FF[Movement Complete]
    EE --> FF
    U --> GG[Movement Failed]
    
    %% Background Processes
    FF --> HH[Trigger Stock Alerts if Low]
    FF --> II[Update Stock History]
    
    %% Stock Monitoring
    JJ[Daily Stock Check] --> KK[Check Expiry Dates]
    KK --> LL{Near Expiry?}
    LL -->|Yes| MM[Generate Expiry Alert]
    LL -->|No| NN[Continue Monitoring]
    
    %% FEFO/FIFO Logic Detail
    subgraph FEFO_LOGIC [FEFO/FIFO Allocation Logic]
        OO[Stock Records for Item + Warehouse]
        OO --> PP[Order by: expiry_date ASC, lot_number ASC]
        PP --> QQ[Take earliest expiring stock first]
        QQ --> RR[Allocate minimum of: available_qty, remaining_needed]
        RR --> SS[Deduct allocated amount]
        SS --> TT{More quantity needed?}
        TT -->|Yes| UU[Move to next stock record]
        TT -->|No| VV[Allocation complete]
        UU --> QQ
    end
    
    V -.-> FEFO_LOGIC
    
    %% Stock Record States
    subgraph STOCK_STATES [Stock Record States]
        WW[available_quantity > 0: Available]
        XX[available_quantity = 0: Empty]
        YY[expiry_date < today: Expired]
        ZZ[expiry_date - today < threshold: Near Expiry]
    end
    
    style A fill:#e1f5fe
    style D fill:#fff3e0
    style O fill:#fff3e0
    style E fill:#e8f5e8
    style P fill:#e8f5e8
    style U fill:#ffebee
    style GG fill:#ffebee
    style FF fill:#e8f5e8
    style FEFO_LOGIC fill:#f3e5f5
    style STOCK_STATES fill:#f9fbe7
```

## Process Description

### 1. Stock Movement Creation
- User creates a new stock movement (DRAFT status)
- Adds movement items with quantities, lot numbers, and expiry dates
- Movement can be IN (receiving stock) or OUT (consuming stock)

### 2. Stock IN Process (Receiving Inventory)
When a stock movement is confirmed for incoming stock:
1. **Find or Create Stock Records**: For each movement item, system looks for existing stock record with same item_sku, warehouse, lot_number, and expiry_date
2. **Add Quantity**: If record exists, add quantity to available_quantity. If not, create new stock record
3. **Update Balances**: Stock balances are updated immediately

### 3. Stock OUT Process (Consuming Inventory)
When a stock movement is confirmed for outgoing stock:
1. **Check Availability**: Verify sufficient stock exists for the item in the warehouse
2. **FEFO/FIFO Allocation**: System automatically allocates stock using First Expired, First Out logic:
   - Get all available stock records for the item/warehouse
   - Order by expiry_date (earliest first), then lot_number
   - Allocate from earliest expiring stock first
3. **Deduct Quantities**: Reduce available_quantity from allocated stock records
4. **Validation**: Ensure no negative stock balances

### 4. FEFO/FIFO Logic Details
```python
# Example allocation for 100 units needed:
# Stock Record 1: lot_number="A001", expiry_date="2025-08-01", available_quantity=60
# Stock Record 2: lot_number="A002", expiry_date="2025-08-15", available_quantity=80

# Allocation Result:
# - Take 60 from Record 1 (fully depletes it)
# - Take 40 from Record 2 (leaves 40 remaining)
```

### 5. Business Rules
- **Immutability**: Once confirmed, stock movements cannot be modified
- **FEFO Priority**: Always consume earliest expiring stock first
- **Lot Traceability**: Complete tracking of lot numbers through the system
- **Negative Stock Prevention**: System prevents negative stock balances
- **Audit Trail**: All stock changes are logged with user and timestamp

### 6. Integration Points
- **StockMovement**: Records the intent and approval of stock changes
- **StockMovementItem**: Details of what items and quantities are involved
- **Stock**: Actual inventory balances with lot/expiry tracking
- **ItemSKU**: Product definitions from catalog
- **Warehouse**: Location tracking

## Stock Record Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: Stock IN movement confirmed
    Created --> Available: available_quantity > 0
    Available --> PartiallyConsumed: Stock OUT (partial)
    PartiallyConsumed --> Available: Stock IN (replenishment)
    PartiallyConsumed --> Empty: Stock OUT (complete)
    Available --> Empty: Stock OUT (complete)
    Empty --> Available: Stock IN (replenishment)
    Available --> Expired: expiry_date passed
    PartiallyConsumed --> Expired: expiry_date passed
    Expired --> [*]: Manual cleanup/disposal
    
    note right of Available
        Normal operational state
        Can be allocated for consumption
    end note
    
    note right of Expired
        Cannot be allocated
        Requires manual intervention
    end note
```
