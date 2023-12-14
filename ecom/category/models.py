from django.db import models

# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=200,unique=True)
    description = models.TextField(max_length=225, blank=True)
    is_visible = models.BooleanField(default=True)
    cat_image = models.ImageField(upload_to='images/category', blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.category_name
    
class Sub_Category(models.Model):
    sub_category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=200,unique=True)
    description = models.TextField(max_length=225, blank=True)
    is_visible = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    cat_image = models.ImageField(upload_to='images/subcategory', blank=True)

    class Meta:
        verbose_name = 'subcategory'
        verbose_name_plural = 'subcategories'
    def __str__(self):
        return self.sub_category_name
