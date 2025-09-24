# Stock Movement Reference Types Update

## Summary

Updated the stock movement reference types to better reflect business operations:

### Changes Made

1. **Removed NONE Reference Type**
   - The NONE reference type has been removed from the system
   - All existing NONE records are automatically converted to ADJUST during migration

2. **Added New Reference Types**
   - **ADJUST**: Default reference type for stock adjustments (no reference_id required)
   - **INBOUND**: For inbound stock movements (no reference_id required)
   - **OUTBOUND**: For outbound stock movements (no reference_id required)
   - **PRODUCTION**: For production-related movements (reference_id required)

### Reference Type Behaviors

#### No Reference ID Required
- `ADJUST`: Stock adjustments and corrections
- `INBOUND`: Incoming stock movements 
- `OUTBOUND`: Outgoing stock movements

#### Reference ID Required
- `PRODUCTION`: Must reference a Production Order ID

### Database Changes

- **Migration 0007_update_reference_types**: 
  - Converts existing NONE records to ADJUST
  - Updates field choices and constraints
  - Maintains data integrity during transition

### Form and Validation Changes

- Default reference type changed from NONE to ADJUST
- Validation updated to allow empty reference_id for ADJUST, INBOUND, OUTBOUND
- Form widgets and help text updated accordingly

### Test Coverage

All tests have been updated to reflect the new reference types:
- Form validation tests
- Model constraint tests
- View integration tests
- Factory defaults updated

### UI Impact

- Stock movement forms now default to ADJUST type
- Reference ID field is conditionally shown based on selected type
- Better user experience with clearer type names

## Migration Path

Existing data is automatically migrated:
- All NONE reference types → ADJUST reference types
- No manual intervention required
- Reverse migration available if needed

## Business Impact

This change provides clearer semantics for stock movements:
- ADJUST: Internal stock corrections
- INBOUND: Receiving stock from suppliers
- OUTBOUND: Shipping stock to customers  
- PRODUCTION: Stock consumed/produced in manufacturing

The system is now more intuitive and better aligned with typical inventory management workflows.