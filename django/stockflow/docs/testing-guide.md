"""
Test Management Commands

Utility commands for running domain-specific tests in StockFlow.

Examples:
    # Run all warehouse tests
    python manage.py test inventory.tests.warehouse
    
    # Run all inventory tests  
    python manage.py test inventory.tests
    
    # Run all catalog tests
    python manage.py test catalog.tests
    
    # Run specific subdomain test
    python manage.py test inventory.tests.warehouse.test_warehouse_model
    
Domain Structure:
    inventory/
    ├── tests/
    │   ├── warehouse/
    │   │   ├── test_warehouse_model.py
    │   │   ├── test_warehouse_form.py
    │   │   └── test_warehouse_create_view.py
    │   └── stock_movement/
    │       └── (future tests)
    
    catalog/
    ├── tests/
    │   ├── category/
    │   ├── item/
    │   └── bom/
    
Author: StockFlow Team
Created: 2025
"""
