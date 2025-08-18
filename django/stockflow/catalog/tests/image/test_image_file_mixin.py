from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from catalog.models.image import ItemImage

class TestImageFileMixin:
    """Mixin to provide helper methods for image file tests"""

    def _create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Create a test image file"""
        image = Image.new('RGB', size, color=color)
        temp_file = BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        return SimpleUploadedFile(
            name,
            temp_file.getvalue(),
            content_type='image/jpeg'
        )
        
    def tearDown(self):
        # ลบไฟล์จริงที่ถูกสร้างใน media storage
        for img in ItemImage.objects.all():
            if img.image and hasattr(img.image, 'path'):
                import os
                try:
                    if os.path.exists(img.image.path):
                        os.remove(img.image.path)
                except Exception:
                    pass