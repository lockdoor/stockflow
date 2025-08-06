# Stock Overview Feature Documentation

## Overview
The Stock Overview feature provides a comprehensive view of inventory balances across all warehouses, organized by item with detailed breakdowns and quick access to lot-level information.

## Features

### 1. Multi-Warehouse Stock Display
- Shows stock balances for each item across all active warehouses
- Displays quantities and lot counts per warehouse
- Provides total stock calculations across all warehouses

### 2. Summary Statistics
- **Total Items**: Count of items with available stock
- **Total Stock Units**: Sum of all stock quantities across warehouses
- **Low Stock Items**: Items with less than 10 units total
- **Active Warehouses**: Number of warehouses with stock data

### 3. Advanced Search & Filtering
- **Real-time Search**: Search by SKU code, item name, or category
- **Quick Filters**: All Items, Low Stock, Raw Materials, Products
- **Search Highlighting**: Visual highlighting of search terms
- **Debounced Input**: Optimized search performance with 300ms delay

### 4. Pagination System
- **5 Items Per Page**: Clean UI with limited display for better usability
- **Smart Pagination**: Previous/Next buttons with page numbers
- **Page Information**: Shows "X to Y of Z items" for clear navigation
- **Keyboard Shortcuts**: Ctrl/Cmd+K for search focus, Escape to clear

### 5. Item Information Display
- SKU code and item name
- Item type badges (Raw, Product, Package)
- Category information
- Unit of measurement

### 6. Enhanced Table Display
- Clean tabular layout with optimized database queries
- Single query with warehouse annotations for better performance
- Warehouse columns showing stock quantities (lot counts removed for cleaner UI)
- Total quantities with low stock warnings
- Professional, data-focused presentation with search highlighting

## URL Structure

```
/inventory/stock/overview/          # Main stock overview page
/inventory/stock/items/             # Item-lot details (existing)
```

## Template Structure

```
inventory/
├── templates/
│   └── inventory/
│       ├── dashboard.html          # Updated with stock overview links
│       └── stock/
│           ├── stock-overview.html # Main overview template
│           └── stock-item-lot.html # Lot details (existing)
```

## View Implementation

### StockOverviewView
- **Location**: `inventory/views/stock_overview_view.py`
- **Template**: `inventory/stock/stock-overview.html`
- **URL Name**: `inventory:stock-overview`

### Key Methods
- `get_optimized_stock_data()`: Single query with warehouse annotations for performance
- Uses `Case/When` for dynamic warehouse quantity aggregation
- Data sorted by total quantity (descending) then SKU code
- Frontend pagination with 5 items per page for clean UI

## Data Structure

The view provides the following context:

```python
{
    'warehouses': [Warehouse objects],
    'stock_overview': [
        {
            'item': ItemSKU,
            'warehouses': [
                {
                    'warehouse__id': int,
                    'total_quantity': Decimal
                }
            ],
            'total_quantity': Decimal
        }
    ],
    'total_items': int,
    'total_stock_value': Decimal,
    'low_stock_count': int
}
```

### Frontend Features
- **JavaScript-powered Search**: Real-time filtering with debouncing
- **Client-side Pagination**: 5 items per page with smooth navigation
- **Search Highlighting**: Visual highlighting of matching terms
- **Event Delegation**: Optimized event handling for pagination
- **Keyboard Shortcuts**: Ctrl/Cmd+K for search, Escape to clear

## Navigation Integration

### Dashboard Integration
- Quick action card in inventory dashboard
- "View detailed stock" links in warehouse summaries

### Breadcrumb Navigation
- Inventory Dashboard → Stock Overview → Item-Lot Details

## Business Logic

### Stock Calculation
- Only includes items with `available_quantity > 0`
- Only shows active items (`status='ACTIVE'`)
- Aggregates quantities by warehouse using `Sum()`

### Low Stock Detection
- Items with total quantity < 10 units
- Visual warning indicators
- Separate filtering option

### Warehouse Display
- Shows all active warehouses as columns
- Empty cells for warehouses without stock
- Lot count information per warehouse

## User Experience Features

### Visual Indicators
- Color-coded item type badges
- Low stock warning icons
- Responsive table design

### Interactive Elements
- **Advanced Search**: Search by SKU, name, or category with highlighting
- **Smart Filtering**: All Items, Low Stock, Raw Materials, Products
- **Pagination Controls**: Clean navigation with page information
- **Keyboard Navigation**: Shortcuts for efficient interaction
- **Responsive Design**: Mobile-friendly with touch support

### Responsive Design
- Mobile-friendly table layout
- Collapsible warehouse columns on small screens
- Touch-friendly action buttons

## Future Enhancements

### Planned Features
1. Export functionality (CSV/Excel)
2. Advanced filtering (by category, type, expiry date)
3. Stock value calculations (with cost data)
4. Real-time stock updates
5. Barcode scanning integration

### Performance Optimizations
1. **Single Query Optimization**: Uses annotations instead of N+1 queries
2. **Frontend Pagination**: Client-side pagination for better UX
3. **Debounced Search**: 300ms delay prevents excessive filtering
4. **Event Delegation**: Efficient event handling for dynamic content

## Related Features

### Connected Components
- **Inventory Dashboard**: Main entry point
- **Stock Movements**: Transaction history
- **Warehouse Management**: Location context

### Data Dependencies
- `Stock` model: Core inventory data
- `ItemSKU` model: Item information
- `Warehouse` model: Location data
- `Category` model: Item categorization

## Usage Examples

### Viewing Stock Overview
1. Navigate to Inventory Dashboard
2. Click "Stock Overview" quick action
3. Review summary statistics
4. Use search and filters to find specific items
5. Navigate through pages using pagination controls

### Searching and Filtering
1. Use search box to find items by SKU, name, or category
2. Click filter buttons (All, Low Stock, Raw, Product)
3. View highlighted search results
4. Use Ctrl/Cmd+K shortcut to focus search
5. Press Escape to clear search

### Analyzing Stock Data
1. Review warehouse-specific quantities in table columns
2. Identify items with low stock warnings
3. Monitor total inventory levels in summary cards
4. Use pagination to browse through all items efficiently

### Identifying Low Stock
1. Click "Low Stock Only" filter
2. Review items below threshold
3. Take action on critical inventory
4. Plan restock activities
