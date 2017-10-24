from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection

# Create your views here.

# /cart/add

class AddCartView(View):
    def post(self, request):
        if not request.user.is_authenticated():
            return JsonResponse({'code':1, 'message':'用户未登陆'})


        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        if not all([sku_id, count]):
            return JsonResponse({'code':2, 'message':'参数不完整'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':3, 'message':'商品不存在'})
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':4, 'message':'参数错误'})

        if count > sku.stock:
            return JsonResponse({'code':5, 'message':'库存不足'})

        redis_conn = get_redis_connection('default')

        user_id = request.user.id

        origin_count = redis_conn.hget('cart_%s' % user_id, sku_id)

        if origin_count is not None:
            count += int(origin_count)
        redis_conn.hset('cart_%s' % user_id, sku_id, count)

        return JsonResponse({'code': 0, 'message': '添加购物车成功'})