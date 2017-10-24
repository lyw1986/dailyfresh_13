from django.shortcuts import render, redirect
from django.views.generic import View
from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner
from goods.models import IndexCategoryGoodsBanner, GoodsSKU, Goods
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.urlresolvers import reverse

from django.core.paginator import Paginator, EmptyPage



# Create your views here.
class IndexView(View):
    def get(self, request):
        context = cache.get('index_page_data')
        if context is None:
            print('没有用上缓存，查询数据库')
            categorys = GoodsCategory.objects.all()

            index_goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            promotions_banners = IndexPromotionBanner.objects.all().order_by('index')

            for category in categorys:
                titile_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by('index')[:4]
                category.title_banners = titile_banners
                image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by('index')[:4]
                category.image_banners = image_banners

            context = {

                "categorys":categorys,
                'index_banners':index_goods_banners,
                'promotion_banners':promotions_banners,
            }
            cache.set('index_page_data', context, 3600)

        cart_num = 0

        if request.user.is_authenticated():

            redis_conn = get_redis_connection('default')

            cart = redis_conn.hgetall('cart_%s' % request.user.id)

            for value in cart.values():
                cart_num += int(value)

        context.update(cart_num=0)

        return render(request, 'index.html', context)

class DetailView(View):
    def get(self, request, sku_id):
        context = cache.get('detail_%s' % sku_id)
        if context is None:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                # from django.http import Http404
                # raise redirect(reverse('goods:index'))
                return redirect(reverse('goods:index'))

            categorys = GoodsCategory.objects.all()

            sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
            if sku_orders:
                for sku_order in sku_orders:
                    sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%H:%S')
                    sku_order.username = sku_order.order.user.username

            else:
                sku_orders = []

            new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]

            goods_skus = sku.goods.goodssku_set.exclude(id=sku_id)

            context = {
                'categorys':categorys,
                'sku':sku,
                'orders':sku_orders,
                'new_skus':new_skus,
                'goods_skus':goods_skus,

            }

            cache.set('detail_%s' % sku_id, context, 3600)

        cart_num = 0

        if request.user.is_authenticated():
            user_id = request.user.id

            redis_conn = get_redis_connection('default')

            cart = redis_conn.hgetall('cart_%s' % user_id)

            for val in cart.values():
                cart_num += int(val)


            redis_conn.lrem('history_%s' % user_id, 0, sku_id)
            redis_conn.lpush('history_%s' % user_id, sku_id)
            redis_conn.ltrim('history_%s' % user_id, 0, 4)

        context.update({'cart_num': cart_num})

        return render(request, 'detail.html', context)


class ListView(View):
    def get(self, request, category_id, page):
        sort = request.GET.get('sort', 'default')
        if sort not in ('price', 'hot'):
            sort = 'default'

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return reverse('goods:index')

        cart_num = 0

        if request.user.is_authenticated():
            user_id = request.user.id

            redis_conn = get_redis_connection('default')

            cart = redis_conn.hgetall('cart_%s' % user_id)
            for val in cart.values():
                cart_num += int(val)

        categorys = GoodsCategory.objects.all()

        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]

        if sort == "price":
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')

        else:
            skus = GoodsSKU.objects.filter(category=category)


        paginator = Paginator(skus, 2)

        page = int(page)

        try:
            page_skus = paginator.page(page)

        except EmptyPage:
            page_skus = paginator.page(1)
            page = 1

        num_pages = paginator.num_pages

        if num_pages <= 5:
            page_list = range(1, num_pages + 1)

        elif page <= 3:
            page_list = range(1, 6)

        elif num_pages - page < 3:
            page_list = range(num_pages-4, num_pages+1)

        else:
            page_list = range(page-2, page+3)


        context = {
            'category': category,
            'categorys': categorys,
            'cart_num': cart_num,
            'new_skus': new_skus,
            'page_skus':page_skus,
            'page_list': page_list,
            'sort': sort
        }

        return render(request, 'list.html', context)

