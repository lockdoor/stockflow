"""
Warehouse Signals

This module contains signal handlers for Warehouse model.
Currently moved permission creation to Warehouse.save() method for better transaction control.

Author: StockFlow Team
Created: 2025
"""

# Permission creation moved to Warehouse.save() method
# for better transaction control and data consistency
