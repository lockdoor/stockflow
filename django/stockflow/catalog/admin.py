from django.contrib import admin

# Register your models here.
from catalog.models.category import Category
from catalog.models.item import ItemSKU

from simple_history.admin import SimpleHistoryAdmin

admin.site.register(Category, SimpleHistoryAdmin)
admin.site.register(ItemSKU, SimpleHistoryAdmin)
