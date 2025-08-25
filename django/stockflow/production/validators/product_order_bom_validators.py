
from common.validators.base import BaseValidator

class ProductionOrderBOMUpdateValidator(BaseValidator):
    """
    Validator to ensure that a ProductionOrderBOM can only be updated under certain conditions.
    """
    def validate(self):
        errors = []
        # Check if the production order status is not DRAFT
        if self.instance.production_order.status != 'DRAFT':
            errors.append("ProductionOrderBOM can only be updated when the production order status is DRAFT.")
        return errors
