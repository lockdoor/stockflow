# Stock Movement Recovery: Quick Reference Guide

## 🚨 Emergency Response Procedures

### Immediate Actions for Critical Issues

#### 1. System-wide Stock Movement Issues
```bash
# Step 1: Assessment
python manage.py check_stock_consistency

# Step 2: Identify scope  
python manage.py check_stock_consistency --warehouse-id [ID]

# Step 3: Recovery (if safe)
python manage.py recover_stock_movements --dry-run
python manage.py recover_stock_movements
```

#### 2. Single Movement Issue
```bash
# For specific movement
python manage.py recover_stock_movements --movement-id [ID] --dry-run
python manage.py recover_stock_movements --movement-id [ID]
```

## 🔧 Common Issue Resolution

### Issue: Movement Stuck in PROCESSING
**Symptoms**: Movement status = 'PROCESSING' for >5 minutes

**Quick Fix**:
```bash
python manage.py recover_stock_movements --movement-id [ID]
```

**Manual Fix (Django shell)**:
```python
from inventory.models.stock_movement import StockMovement

movement = StockMovement.objects.get(id=[ID])
movement.recover()  # Attempts automatic recovery
# OR
movement.mark_as_failed()  # Manual marking if recovery impossible
```

### Issue: Balance Discrepancies
**Symptoms**: Stock totals don't match movement history

**Quick Fix**:
```bash
python manage.py check_stock_consistency --fix
```

**Manual Investigation**:
```python
from inventory.models.stock import Stock
from inventory.models.stock_movement_item import StockMovementItem

# Check expected vs actual
expected = StockMovementItem.objects.filter(
    item_sku=item, stock_movement__warehouse=warehouse
).aggregate(total=models.Sum('quantity'))['total']

actual = Stock.get_total_stock(item, warehouse)
print(f"Expected: {expected}, Actual: {actual}")
```

### Issue: Deadlock Errors
**Symptoms**: "deadlock detected" errors in logs

**Quick Fix**:
```python
# In Django shell - retry failed movements
failed_movements = StockMovement.objects.filter(status='FAILED')
for movement in failed_movements:
    try:
        movement.recover()
        print(f"Recovered movement {movement.id}")
    except Exception as e:
        print(f"Failed to recover {movement.id}: {e}")
```

### Issue: HTMX Redirect Not Working
**Symptoms**: Users don't see confirmation after submit

**Code Fix** (in view):
```python
if request.headers.get('HX-Request'):
    # Return redirect header for HTMX
    response = HttpResponse()
    response['HX-Redirect'] = reverse('inventory:stock_movement_list')
    return response
else:
    # Normal redirect for non-HTMX requests
    return redirect('inventory:stock_movement_list')
```

## 🔍 Diagnostic Commands

### Check System Health
```bash
# Overall health check
python manage.py check_stock_consistency

# Specific warehouse
python manage.py check_stock_consistency --warehouse-id 1

# Verbose output
python manage.py check_stock_consistency --verbosity 2
```

### Find Problematic Movements
```sql
-- In database console
SELECT id, status, updated_at, confirmed_at 
FROM inventory_stockmovement 
WHERE status IN ('PROCESSING', 'FAILED')
ORDER BY updated_at DESC;

-- Movements stuck for >5 minutes
SELECT id, status, updated_at
FROM inventory_stockmovement 
WHERE status = 'PROCESSING' 
AND updated_at < NOW() - INTERVAL '5 minutes';
```

### Check Stock Consistency
```python
# In Django shell
from inventory.models.stock_movement import StockMovement
from inventory.models.stock import Stock

# Count by status
for status in StockMovement.Status:
    count = StockMovement.objects.filter(status=status).count()
    print(f"{status}: {count}")

# Check for orphaned stocks
orphaned = Stock.objects.filter(
    available_quantity=0
).count()
print(f"Zero-quantity stock records: {orphaned}")
```

## 📋 Preventive Maintenance

### Daily Checks (Cron Job)
```bash
#!/bin/bash
# Daily stock consistency check
0 2 * * * cd /path/to/stockflow && python manage.py check_stock_consistency >> /var/log/stock_check.log 2>&1
```

### Weekly Cleanup
```bash
#!/bin/bash
# Weekly cleanup of old failed movements
python manage.py shell -c "
from inventory.models.stock_movement import StockMovement
from django.utils import timezone
from datetime import timedelta

old_failed = StockMovement.objects.filter(
    status='FAILED',
    updated_at__lt=timezone.now() - timedelta(days=7)
)
print(f'Found {old_failed.count()} old failed movements')
# old_failed.delete()  # Uncomment to actually delete
"
```

### Monitor Performance
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE query LIKE '%stock%' 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check deadlock stats
SELECT datname, deadlocks 
FROM pg_stat_database 
WHERE datname = 'stockflow';
```

## 🚨 Emergency Contacts & Escalation

### Level 1: Self-Service Recovery
- Use management commands
- Check documentation
- Review logs

### Level 2: Manual Intervention Required  
- Balance corrections needed
- Complex data inconsistencies
- Multiple failed recoveries

### Level 3: Database Expert Required
- Deadlock patterns
- Performance issues
- Schema modifications needed

## 📊 Monitoring Dashboard Queries

### Key Metrics
```sql
-- Movements by status (last 24h)
SELECT status, COUNT(*) as count
FROM inventory_stockmovement 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;

-- Average processing time
SELECT 
    AVG(EXTRACT(EPOCH FROM (updated_at - confirmed_at))) as avg_seconds
FROM inventory_stockmovement 
WHERE status = 'COMPLETED' 
AND confirmed_at IS NOT NULL;

-- Failed movement rate
SELECT 
    (COUNT(CASE WHEN status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*)) as failure_rate
FROM inventory_stockmovement 
WHERE created_at > NOW() - INTERVAL '24 hours';
```

### Health Check API
```python
# Add to views.py for monitoring endpoint
def stock_health_check(request):
    """Health check endpoint for monitoring systems"""
    
    stuck_movements = StockMovement.objects.filter(
        status=StockMovement.Status.PROCESSING,
        updated_at__lt=timezone.now() - timedelta(minutes=5)
    ).count()
    
    failed_movements = StockMovement.objects.filter(
        status=StockMovement.Status.FAILED,
        updated_at__gt=timezone.now() - timedelta(hours=1)
    ).count()
    
    health_data = {
        'status': 'healthy' if stuck_movements == 0 and failed_movements < 5 else 'degraded',
        'stuck_movements': stuck_movements,
        'recent_failures': failed_movements,
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(health_data)
```

## 🔄 Recovery Success Verification

### After Running Recovery Commands
```bash
# 1. Verify no stuck movements
python manage.py check_stock_consistency

# 2. Check movement status distribution  
python manage.py shell -c "
from inventory.models.stock_movement import StockMovement
for status in StockMovement.Status:
    count = StockMovement.objects.filter(status=status).count()
    print(f'{status}: {count}')
"

# 3. Verify stock balances
python manage.py shell -c "
from inventory.models.stock import Stock
from catalog.models.item import ItemSKU

total_items = ItemSKU.objects.count()
items_with_stock = Stock.objects.values('item_sku').distinct().count()
print(f'Items with stock: {items_with_stock}/{total_items}')
"
```

### Test Movement Confirmation
```python
# In Django shell - test a simple movement
from inventory.models.stock_movement import StockMovement
from django.contrib.auth.models import User

user = User.objects.first()
movement = StockMovement.objects.filter(status='CONFIRMED').first()

if movement:
    try:
        movement.confirm(user)
        print("✅ Movement confirmation working")
    except Exception as e:
        print(f"❌ Movement confirmation failed: {e}")
```

---

**Last Updated**: July 30, 2025  
**For 24/7 Support**: Check project README for contact information  
**Emergency Escalation**: Contact database administrator immediately for Level 3 issues
