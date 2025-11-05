from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Product, Cart, CartItem
from .serializers import ProductSerializer, CartSerializer, CartItemSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    # Все пользователи могут работать (пока нет auth)


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all().order_by("-created_at")
    serializer_class = CartSerializer

    def create(self, request, *args, **kwargs):
        cart = Cart.objects.create()
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

