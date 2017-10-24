from django.contrib import admin

# Register your models here.
from goods.models import Goods,GoodsCategory,GoodsSKU,GoodsImage
from goods.models import IndexGoodsBanner, IndexCategoryGoodsBanner, IndexPromotionBanner
from celery_tasks.tasks import generate_static_index_html
from django.core.cache import cache

class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()

        generate_static_index_html.delay()

        cache.delete('index_page_data')

    def delete_model(self, request, obj):

        obj.delete()

        generate_static_index_html.delay()

        cache.delete('index_page_data')

class GoodsCategoryAdmin(BaseAdmin):
    """商品分类信息的管理类"""
    # 在这里填充控制amdin站点的展示效果
    pass


class IndexPromotionBannerAdmin(BaseAdmin):
    """"""
    pass
admin.site.register(GoodsCategory)
admin.site.register(Goods)
admin.site.register(GoodsSKU)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner)
admin.site.register(IndexCategoryGoodsBanner)
admin.site.register(IndexPromotionBanner)