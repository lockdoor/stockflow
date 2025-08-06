# Stock Views Testing Guide

This directory contains comprehensive test suites for the Stock Views functionality in the StockFlow application.

## Overview

The stock views testing framework validates the critical components of the stock management system, ensuring data integrity, performance optimization, and user experience consistency.

## Test Files

### `test_stock_overview_view.py`
Tests for the **StockOverviewView** which provides a comprehensive dashboard of stock balances across warehouses.

**Key Test Categories:**
- **Authentication & Authorization**: Login requirements and access control
- **Template Rendering**: Correct template usage and HTML structure
- **Context Data**: Proper data passing to templates
- **Query Optimization**: Database query efficiency validation
- **Frontend Integration**: JSON data format for JavaScript processing
- **Business Logic**: Stock filtering, ordering, and calculations
- **Edge Cases**: Empty data sets, inactive items/warehouses

**Test Coverage:**
- 14 comprehensive test methods
- Authentication flow validation
- Optimized query performance (2 queries maximum)
- Summary statistics calculations
- Active items and warehouses filtering
- Low stock detection logic
- Frontend search data JSON formatting

### `test_stock_item_detail_view.py`
Tests for the **StockItemDetailView** which displays detailed lot information for specific items.

**Key Test Categories:**
- **Item Lot Management**: Warehouse-based lot grouping
- **Data Validation**: Lot details, quantities, and expiry dates
- **User Interface**: Template rendering and content display
- **Performance**: Query optimization for lot details
- **Error Handling**: Non-existent items and edge cases

**Test Coverage:**
- 15 comprehensive test methods
- Warehouse lot grouping validation
- Zero-quantity lot exclusion
- Summary statistics for individual items
- Expiry date display verification
- Optimized database queries (1 query for lot data)

## Test Data Management

### Model Creation Strategy
Tests use proper Django model creation patterns with consideration for:
- **AuditableMixin**: All models require `created_by` and `updated_by` fields
- **Business Rules**: ItemSKU products must start as DRAFT before activation
- **Validation Constraints**: Warehouse activation/deactivation rules
- **Data Integrity**: Stock cannot be created for inactive items/warehouses

### Test User Setup
```python
self.user = User.objects.create_user(
    username='testuser',
    email='test@example.com', 
    password='testpass123'
)
```

### Sample Test Data Structure
- **Categories**: Test categories with proper audit fields
- **Warehouses**: Active and inactive warehouses for filtering tests
- **Items**: Products (DRAFT→ACTIVE) and Raw materials with different types
- **Stock Records**: Various lot numbers, quantities, and expiry dates

## Running Tests

### Individual Test Files
```bash
# Stock Overview View tests
python manage.py test inventory.tests.stock.test_stock_overview_view -v 2

# Stock Item Detail View tests  
python manage.py test inventory.tests.stock.test_stock_item_detail_view -v 2
```

### All Stock Tests
```bash
# Run all stock-related tests
python manage.py test inventory.tests.stock -v 2
```

### Performance Testing
```bash
# Focus on query optimization tests
python manage.py test inventory.tests.stock -k "optimized_query" -v 2
```

## Test Database Optimization

### Key Performance Metrics
- **StockOverviewView**: Maximum 2 database queries
  1. Warehouses retrieval
  2. Items with aggregated stock data (includes category select_related)

- **StockItemDetailView**: Maximum 1 database query
  1. Stock records with warehouse select_related

### Query Optimization Validation
Tests include `assertNumQueries()` assertions to ensure:
- Minimal database hits
- Proper use of `select_related()` and `prefetch_related()`
- Efficient aggregation using Django's `Case/When` expressions

## Coverage Areas

### Functional Testing
- ✅ View accessibility and authentication
- ✅ Template rendering and content validation
- ✅ Context data completeness
- ✅ URL routing and parameter handling
- ✅ Error handling (404s, invalid data)

### Performance Testing  
- ✅ Database query optimization
- ✅ Response time validation
- ✅ Memory usage for large datasets

### Integration Testing
- ✅ Frontend JSON data format
- ✅ Search functionality data preparation
- ✅ Pagination context setup
- ✅ Breadcrumb navigation

### Business Logic Testing
- ✅ Stock quantity calculations
- ✅ Warehouse-based grouping
- ✅ Active/inactive filtering
- ✅ Low stock detection
- ✅ Summary statistics accuracy

## Best Practices Demonstrated

1. **Comprehensive Setup**: Proper test data creation following business rules
2. **Isolation**: Each test is independent with consistent setUp/tearDown
3. **Realistic Data**: Test scenarios mirror real-world usage patterns
4. **Edge Case Coverage**: Empty datasets, inactive records, zero quantities
5. **Performance Awareness**: Query count validation and optimization testing
6. **User Experience**: Template content and navigation flow validation

## Future Enhancements

Potential areas for test expansion:
- **Stress Testing**: Large dataset performance validation
- **Concurrent Access**: Multi-user scenario testing  
- **API Integration**: RESTful endpoint testing if added
- **Caching**: Cache invalidation and performance testing
- **Mobile Responsiveness**: Template rendering across devices

## Related Documentation

- [Stock Management Flow](../../docs/stock-management-flow.md)
- [Stock Integration Flow](../../docs/stock-integration-flow.md)
- [Testing Guide](../../docs/testing-guide.md)
- [Template Structure Guidelines](../../docs/template-structure-guidelines.md)

---

**Total Test Coverage**: 29 test methods across stock view functionality
**Database Efficiency**: Validated minimal query patterns
**Business Rule Compliance**: All stock management constraints tested
