
from common.validators.base import BaseValidator
# from production.models.production_order import ProductionOrder


class ProductionOrderInitialStatusValidator(BaseValidator):
	"""
	Validator to ensure that a ProductionOrder can only be created with status DRAFT.
	Returns error list if status is not DRAFT on initial creation.
	"""
	def validate(self):
		errors = []
		# Only validate on initial creation (no pk yet)
		if self.instance.pk is None:
			if self.instance.status != 'DRAFT':
				errors.append("ProductionOrder initial status must be DRAFT.")
		return errors

class ProductionOrderStatusDraftToCreatedValidator(BaseValidator):
	"""
	Validator to ensure that a ProductionOrder can only be changed from DRAFT to CREATED
	if it has at least one associated ItemSKU.
	"""
	def validate(self):
		errors = []
		from production.models import ProductionOrder
			
		if self.instance.pk:
			original: ProductionOrder = ProductionOrder.objects.get(id=self.instance.pk)

			if not original:
				errors.append("ProductionOrder not found.")

			if original.status == ProductionOrder.Status.DRAFT \
   				and self.instance.status not in [ProductionOrder.Status.CREATED, ProductionOrder.Status.DRAFT]:
				errors.append("ProductionOrder must change from DRAFT to CREATED.")

			if self.instance.status == ProductionOrder.Status.CREATED and original.bom_count <= 0:
				errors.append("ProductionOrder must have at least one BOM item to change status from DRAFT to CREATED.")
		
		return errors

class ProductionOrderCanNotChangeWareHouseValidator(BaseValidator):
	"""
	Validator to ensure that a ProductionOrder's warehouse cannot be changed
	once the order is created.
	"""
	def validate(self):
		errors = []
		from production.models import ProductionOrder

		if self.instance.pk:
			original: ProductionOrder = ProductionOrder.objects.get(id=self.instance.pk)

			if not original:
				errors.append("ProductionOrder not found.")

			if original.warehouse_id != self.instance.warehouse_id:
				errors.append("Cannot change warehouse of an existing ProductionOrder.")

		return errors