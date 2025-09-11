"""
WIP Return Lot Number Generator

Utility functions for generating lot numbers when returning WIP materials to inventory.
"""

from datetime import datetime
from typing import Optional


def generate_wip_return_lot_number(production_order_id: int, item_sku_id: Optional[int] = None) -> str:
    """
    Generate unique lot number for WIP material return
    
    Args:
        production_order_id (int): Production order ID
        item_sku_id (int, optional): Item SKU ID for additional uniqueness
        
    Returns:
        str: Generated lot number in format WIP-PO{id}-RET-{timestamp}[-item_id]
        
    Example:
        >>> generate_wip_return_lot_number(123)
        'WIP-PO123-RET-20250910143022'
        >>> generate_wip_return_lot_number(123, 456)
        'WIP-PO123-RET-20250910143022-ITM456'
    """
    # Generate timestamp with microseconds for better uniqueness
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]  # Include first 4 digits of microseconds
    
    # Generate base lot number with item_sku_id if provided
    if item_sku_id:
        base_lot = f"WIP-PO{production_order_id:03d}-RET-{timestamp}-ITM{item_sku_id}"
    else:
        base_lot = f"WIP-PO{production_order_id:03d}-RET-{timestamp}"
    
    # Ensure uniqueness by checking existing lot numbers
    from inventory.models import StockMovementItem
    
    lot_number = base_lot
    counter = 1
    
    # Handle concurrent requests by adding counter suffix if needed (unlikely with microseconds)
    while StockMovementItem.objects.filter(lot_number=lot_number).exists():
        lot_number = f"{base_lot}-{counter:02d}"
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 99:
            # Add additional randomness
            import random
            random_suffix = random.randint(1000, 9999)
            lot_number = f"{base_lot}-{random_suffix}"
            break
    
    return lot_number


def validate_wip_return_lot_format(lot_number: str) -> bool:
    """
    Validate if lot number follows WIP return format
    
    Args:
        lot_number (str): Lot number to validate
        
    Returns:
        bool: True if valid WIP return lot format
        
    Example:
        >>> validate_wip_return_lot_format('WIP-PO123-RET-20250910143022')
        True
        >>> validate_wip_return_lot_format('WIP-PO123-RET-20250910143022-ITM456')
        True
        >>> validate_wip_return_lot_format('REGULAR-LOT-001')
        False
    """
    import re
    
    # Pattern: WIP-PO{digits}-RET-{timestamp}[optional-item][optional-counter]
    # Examples:
    # - WIP-PO123-RET-20250910143022
    # - WIP-PO123-RET-20250910143022-ITM456
    # - WIP-PO123-RET-20250910143022-01
    # - WIP-PO123-RET-20250910143022-ITM456-01
    pattern = r'^WIP-PO\d{3,}-RET-\d{14,18}(-ITM\d+)?(-\d{2,4})?$'
    
    return bool(re.match(pattern, lot_number))


def extract_production_order_from_lot(lot_number: str) -> Optional[int]:
    """
    Extract production order ID from WIP return lot number
    
    Args:
        lot_number (str): WIP return lot number
        
    Returns:
        int: Production order ID, or None if not a WIP return lot
        
    Example:
        >>> extract_production_order_from_lot('WIP-PO123-RET-20250910143022')
        123
        >>> extract_production_order_from_lot('REGULAR-LOT-001')
        None
    """
    import re
    
    # Extract PO number from lot format
    pattern = r'^WIP-PO(\d+)-RET-'
    match = re.match(pattern, lot_number)
    
    if match:
        return int(match.group(1))
    
    return None


def get_wip_return_lots_for_production_order(production_order_id: int) -> list:
    """
    Get all WIP return lot numbers for a specific production order
    
    Args:
        production_order_id (int): Production order ID
        
    Returns:
        list: List of lot numbers that were generated for WIP returns
    """
    from inventory.models import StockMovementItem
    
    # Find all lot numbers matching the WIP return pattern for this PO
    lot_pattern = f"WIP-PO{production_order_id:03d}-RET-%"
    
    return list(
        StockMovementItem.objects.filter(
            lot_number__startswith=f"WIP-PO{production_order_id:03d}-RET-"
        ).values_list('lot_number', flat=True).distinct()
    )
