from django import forms
from django.core.exceptions import ValidationError
from catalog.models.category import Category

class CategoryForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        """Initialize form with optional user parameter"""
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Set initial value for is_active if not provided and not updating existing instance
        if not self.instance.pk and 'is_active' not in self.initial:
            self.fields['is_active'].initial = True
    
    class Meta:
        model = Category
        fields = ['name', 'note', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter category name',
                'maxlength': '100',
                'class': 'form-control'
            }),
            'note': forms.Textarea(attrs={
                'placeholder': 'Enter optional note',
                'rows': 3,
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Category Name',
            'note': 'Note (Optional)',
            'is_active': 'Active Category',
        }
    
    def save(self, commit=True):
        """Override save to handle business logic errors and set audit fields"""
        instance = super().save(commit=False)
        
        # Set audit fields if user is provided
        if self.user:
            if not instance.pk:  # New instance
                instance.created_by = self.user
            instance.updated_by = self.user
        
        if commit:
            try:
                instance.save()
            except (ValueError, ValidationError) as e:
                # Convert model ValueError and other errors to form ValidationError
                raise ValidationError(str(e))
        
        return instance
