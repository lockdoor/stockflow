from django import forms
from catalog.models.image import ItemImage
from catalog.models.item import ItemSKU

class ItemImageForm(forms.ModelForm):
    """
    Form for creating and updating ItemImage instances.
    Form validation is minimal as business logic validation is handled at the model level.
    """
    
    # Override item field to use active items only
    item = forms.ModelChoiceField(
        queryset=ItemSKU.objects.filter(status='ACTIVE'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True,
        label="Item",
        help_text="Select the item for this image"
    )

    class Meta:
        model = ItemImage
        fields = ['item', 'image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'placeholder': 'Choose image file'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image caption (optional)',
                'maxlength': 255
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'image': 'Upload an image file (JPG, PNG, GIF, BMP, WebP). Max size: 10MB, Max dimensions: 4000x4000px',
            'caption': 'Optional description for the image (max 255 characters)',
            'is_primary': 'Check to set this as the primary image for the item'
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with custom behavior"""
        # Extract item from kwargs if provided
        item = kwargs.pop('item', None)
        super().__init__(*args, **kwargs)
        
        # If item is provided, limit item field choices to that item only
        if item:
            self.fields['item'].queryset = ItemSKU.objects.filter(id=item.id)
            self.fields['item'].initial = item
        
        # If editing existing image, don't allow changing the item
        if self.instance and self.instance.pk:
            self.fields['item'].widget.attrs['disabled'] = True
            self.fields['item'].help_text = "Item cannot be changed after creation"

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


class ItemImageBulkUploadForm(forms.Form):
    """
    Simple form for uploading multiple images one by one
    """
    
    item = forms.ModelChoiceField(
        queryset=ItemSKU.objects.filter(status='ACTIVE'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True,
        label="Item",
        help_text="Select the item for these images"
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
        # Extract item from kwargs if provided
        item = kwargs.pop('item', None)
        super().__init__(*args, **kwargs)
        
        # If item is provided, limit item field choices to that item only
        if item:
            self.fields['item'].queryset = ItemSKU.objects.filter(id=item.id)
            self.fields['item'].initial = item
        
        # If editing existing image, don't allow changing the item
        # if self.instance and self.instance.pk:
        #     self.fields['item'].widget.attrs['disabled'] = True
        #     self.fields['item'].help_text = "Item cannot be changed after creation"

    # We'll handle multiple files in the view using request.FILES.getlist()

    def clean_images(self):
        """Validate uploaded images"""
        images = self.files.getlist('images')
        
        if not images:
            raise forms.ValidationError("Please select at least one image file.")
        
        # Validate each image
        for image in images:
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
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
        """Save multiple images for the selected item"""
        item = self.cleaned_data['item']
        images = self.files.getlist('images')  # Get from request files directly
        set_first_as_primary = self.cleaned_data['set_first_as_primary']
        
        created_images = []
        
        for i, image in enumerate(images):
            # Set as primary only for the first image if requested
            is_primary = set_first_as_primary and i == 0
            
            item_image = ItemImage(
                item=item,
                image=image,
                is_primary=is_primary,
                created_by=user,
                updated_by=user
            )
            item_image.save()
            created_images.append(item_image)
        
        return created_images


class ItemImageUpdateForm(forms.ModelForm):
    """
    Simple form for updating image caption and primary status
    """
    
    class Meta:
        model = ItemImage
        fields = ['caption', 'is_primary']
        widgets = {
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image caption (optional)',
                'maxlength': 255
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'caption': 'Optional description for the image (max 255 characters)',
            'is_primary': 'Check to set this as the primary image for the item'
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
