from django.contrib import admin
from .models import Category, Product, Ingredient, ProductIngredient, IngredientCategory

@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_extra')
    list_filter = ('is_extra',)
    search_fields = ('name',)
    list_editable = ('is_extra',)

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_extra', 'is_active')
    list_filter = ('category', 'is_extra', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_extra', 'is_active')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1
    fields = ('ingredient', 'group_name', 'is_required', 'max_quantity')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "ingredient":
            kwargs["queryset"] = Ingredient.objects.filter(is_active=True).select_related('category')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    inlines = [ProductIngredientInline]
    list_editable = ('price', 'is_active')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'emoji', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('emoji', 'is_active')
