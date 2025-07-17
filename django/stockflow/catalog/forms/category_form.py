from django import forms
from django.core.exceptions import ValidationError
from catalog.models.category import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'note']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter category name',
                'maxlength': '100'
            }),
            'note': forms.Textarea(attrs={
                'placeholder': 'Enter optional note',
                'rows': 3
            }),
        }
        labels = {
            'name': 'Category Name',
            'note': 'Note (Optional)',
        }
    
    def save(self, commit=True):
        """Override save to handle business logic errors"""
        instance = super().save(commit=False)
        
        if commit:
            try:
                # Set user fields (should be set by view)
                # instance.created_by and instance.updated_by should be set by view
                instance.save()
            except (ValueError, Exception) as e:
                # Convert model ValueError and other errors to form ValidationError
                raise ValidationError(str(e))
        
        return instance
