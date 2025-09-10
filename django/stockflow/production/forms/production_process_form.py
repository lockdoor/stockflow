from django import forms
from django.core.exceptions import ValidationError
from production.models.production_process import ProductionProcess
from production.models.production_result import ProductionResult
from production.models.production_loss import ProductionLoss


class ProductionProcessForm(forms.ModelForm):
    """Form for creating and editing production processes"""
    
    class Meta:
        model = ProductionProcess
        fields = [
            'process_name',
            'note',
            'started_at',
            'finished_at',
        ]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'finished_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.production_order = kwargs.pop('production_order', None)
        super().__init__(*args, **kwargs)


class ProductionResultForm(forms.ModelForm):
    """Form for adding production results"""
    
    class Meta:
        model = ProductionResult
        fields = ['production_process', 'item_sku', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.production_process = kwargs.pop('production_process', None)
        self.production_order = kwargs.pop('production_order', None)
        super().__init__(*args, **kwargs)
        
        if self.production_process:
            self.fields['production_process'].initial = self.production_process
            self.fields['production_process'].widget = forms.HiddenInput()
        
        # กรอง item_sku ให้แสดงเฉพาะ products ที่อยู่ใน BOM ของ production order
        if self.production_order:
            from production.models.production_order_bom import ProductionOrderBOM
            
            # หา products ที่อยู่ใน BOM ของ production order นี้
            bom_products = ProductionOrderBOM.objects.filter(
                production_order=self.production_order
            ).values_list('item_sku', flat=True)
            
            # กรอง queryset ให้แสดงเฉพาะ products ที่อยู่ใน BOM
            self.fields['item_sku'].queryset = self.fields['item_sku'].queryset.filter(
                id__in=bom_products
            )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        return quantity


class ProductionLossForm(forms.ModelForm):
    """Form for adding production losses"""
    
    class Meta:
        model = ProductionLoss
        fields = ['production_process', 'item_sku', 'quantity', 'reason']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'reason': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.production_process = kwargs.pop('production_process', None)
        self.production_order = kwargs.pop('production_order', None)
        super().__init__(*args, **kwargs)
        
        if self.production_process:
            self.fields['production_process'].initial = self.production_process
            self.fields['production_process'].widget = forms.HiddenInput()
        
        # กรอง item_sku ให้แสดงเฉพาะ materials ที่อยู่ใน WIP ของ production order
        if self.production_order:
            from production.models.wip_stock_movement import WIPStockMovement
            
            # หา materials ที่มีใน WIP ของ production order นี้
            wip_materials = WIPStockMovement.objects.filter(
                production_order=self.production_order,
                movement_type=WIPStockMovement.MovementType.IN
            ).values_list('item_sku', flat=True).distinct()
            
            # กรอง queryset ให้แสดงเฉพาะ materials ที่มีใน WIP
            self.fields['item_sku'].queryset = self.fields['item_sku'].queryset.filter(
                id__in=wip_materials
            )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        return quantity


class ProductionProcessUnifiedForm(forms.ModelForm):
    """Unified form for production process with results and losses"""
    
    class Meta:
        model = ProductionProcess
        fields = [
            'process_name',
            'note',
            'started_at',
            'finished_at',
        ]
        widgets = {
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'finished_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.production_order = kwargs.pop('production_order', None)
        super().__init__(*args, **kwargs)
        
        if self.production_order:
            # Set production_order for the instance
            if self.instance and not self.instance.pk:
                self.instance.production_order = self.production_order
