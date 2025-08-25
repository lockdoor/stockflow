from django.db import models

class ProductionStatusMixin(models.Model):
    """
    Mixin to add production status fields and methods to a model.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'  # Initial state
        CREATED = 'CREATED', 'Created'  # After creation
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'  # During production tracking by start time
        PAUSED = 'PAUSED', 'Paused'  # Production paused
        COMPLETED = 'COMPLETED', 'Completed'  # Finished production tracking by finished time
        CANCELLED = 'CANCELLED', 'Cancelled'  # Production halted

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Current status of the production order"
    )

    class Meta:
        abstract = True
