"""
Stock Movement Image Forms

Forms for creating and updating StockMovementImage instances.
Form validation is minimal as business logic validation is handled at the model level.

Author: StockFlow Team
Created: 2025
"""

from django import forms
from inventory.models.stock_movement_image import StockMovementImage
from inventory.models.stock_movement import StockMovement


class StockMovementImageForm(forms.ModelForm):
    """
    Form for creating and updating StockMovementImage instances.
    Form validation is minimal as business logic validation is handled at the model level.
    """
    
    # Override stock_movement field to use non-failed movements only
    stock_movement = forms.ModelChoiceField(
        queryset=StockMovement.objects.exclude(status='FAILED'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True,
        label="Stock Movement",
        help_text="Select the stock movement for this image"
    )

    class Meta:
        model = StockMovementImage
        fields = ['stock_movement', 'image', 'caption', 'is_primary', 'note']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,application/pdf',
                'placeholder': 'Choose image or document file'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image caption (optional)',
                'maxlength': 255
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter additional notes about this document (optional)',
                'rows': 3
            })
        }
        help_texts = {
            'image': 'Upload an image or PDF file (JPG, PNG, GIF, PDF). Max size: 10MB',
            'caption': 'Optional description for the document (max 255 characters)',
            'is_primary': 'Check to set this as the primary document for the stock movement',
            'note': 'Additional notes about the document or image'
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with custom behavior"""
        # Extract stock_movement from kwargs if provided
        stock_movement = kwargs.pop('stock_movement', None)
        super().__init__(*args, **kwargs)
        
        # If stock_movement is provided, limit stock_movement field choices to that movement only
        if stock_movement:
            self.fields['stock_movement'].queryset = StockMovement.objects.filter(id=stock_movement.id)
            self.fields['stock_movement'].initial = stock_movement
        
        # If editing existing image, don't allow changing the stock movement
        if self.instance and self.instance.pk:
            self.fields['stock_movement'].widget.attrs['disabled'] = True
            self.fields['stock_movement'].help_text = "Stock movement cannot be changed after creation"

    def save(self, commit=True):
        """Save with user context"""
        instance = super().save(commit=False)
        
        # Set created_by and updated_by if user is available
        if hasattr(self, '_user') and self._user:
            if not instance.pk:  # New instance
                instance.created_by = self._user
            instance.updated_by = self._user
        
        if commit:
            instance.save()
        
        return instance

    def set_user(self, user):
        """Set the user for audit fields"""
        self._user = user


class StockMovementImageBulkUploadForm(forms.Form):
    """
    Simple form for uploading multiple images one by one for a stock movement
    """
    
    stock_movement = forms.ModelChoiceField(
        queryset=StockMovement.objects.exclude(status='FAILED'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True,
        label="Stock Movement",
        help_text="Select the stock movement for these images"
    )
    
    set_first_as_primary = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        initial=True,
        label="Set first image as primary",
        help_text="Check to set the first uploaded image as primary"
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize form with custom behavior"""
        # Extract stock_movement from kwargs if provided
        stock_movement = kwargs.pop('stock_movement', None)
        super().__init__(*args, **kwargs)
        
        # If stock_movement is provided, limit stock_movement field choices to that movement only
        if stock_movement:
            self.fields['stock_movement'].queryset = StockMovement.objects.filter(id=stock_movement.id)
            self.fields['stock_movement'].initial = stock_movement

    def clean_images(self):
        """Validate uploaded images"""
        images = self.files.getlist('images')
        
        if not images:
            raise forms.ValidationError("Please select at least one image or document file.")
        
        # Validate each image/document
        for image in images:
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
            import os
            file_extension = os.path.splitext(image.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f"Invalid file extension '{file_extension}' for '{image.name}'. "
                    f"Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if image.size > max_size:
                raise forms.ValidationError(
                    f"File '{image.name}' is too large ({image.size/1024/1024:.1f}MB). "
                    f"Maximum size is {max_size/1024/1024:.1f}MB."
                )
        
        return images

    def save(self, user=None):
        """Save multiple images for the selected stock movement"""
        stock_movement = self.cleaned_data['stock_movement']
        images = self.files.getlist('images')  # Get from request files directly
        set_first_as_primary = self.cleaned_data['set_first_as_primary']
        
        created_images = []
        
        for i, image in enumerate(images):
            # Set as primary only for the first image if requested
            is_primary = set_first_as_primary and i == 0
            
            stock_movement_image = StockMovementImage(
                stock_movement=stock_movement,
                image=image,
                is_primary=is_primary,
                created_by=user,
                updated_by=user
            )
            stock_movement_image.save()
            created_images.append(stock_movement_image)
        
        return created_images


class StockMovementImageUpdateForm(forms.ModelForm):
    """
    Simple form for updating image caption, primary status, and note
    """
    
    class Meta:
        model = StockMovementImage
        fields = ['caption', 'is_primary', 'note']
        widgets = {
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image caption (optional)',
                'maxlength': 255
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter additional notes about this document (optional)',
                'rows': 3
            })
        }
        help_texts = {
            'caption': 'Optional description for the document (max 255 characters)',
            'is_primary': 'Check to set this as the primary document for the stock movement',
            'note': 'Additional notes about the document or image'
        }

    def save(self, commit=True):
        """Save with user context"""
        instance = super().save(commit=False)
        
        # Set updated_by if user is available
        if hasattr(self, '_user') and self._user:
            instance.updated_by = self._user
        
        if commit:
            instance.save()
        
        return instance

    def set_user(self, user):
        """Set the user for audit fields"""
        self._user = user