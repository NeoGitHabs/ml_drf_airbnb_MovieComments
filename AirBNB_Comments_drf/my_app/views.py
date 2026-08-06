from rest_framework import generics, permissions, views, status
from .filters import PropertyFilter
from .permissions import IsOwner, IsGuest
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, LoginSerializer
from .models import UserProfile, City, Property, Images, Booking, Review, FavoriteItem #, Amenity
from .serializers import (UserProfileSerializers, UserProfileUpdateSerializers, CitySerializers,
                          PropertySerializers, PropertyDetailSerializers, BookingListSerializers,
                          BookingCreateSerializers, ReviewListSerializers, ReviewCreateSerializers,
                          FavoriteItemListSerializer, PropertyUpdateSerializers, PropertyCreateSerializers) #, AmenitySerializers


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CustomLoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data
        return Response(serializer.data, status=status.HTTP_200_OK)

class LogoutView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
# ------------------------------------------------------------------------------------
class UserProfileAPIView(generics.ListAPIView):
    serializer_class = UserProfileSerializers

    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)

class UserProfileUpdateAPIView(generics.UpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileUpdateSerializers

    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)

class PropertyListAPIView(generics.ListAPIView):
    queryset = Property.objects.all().select_related('city').prefetch_related('reviews')
    serializer_class = PropertySerializers

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = PropertyFilter
    ordering_fields = ['price_per_night', 'title', 'max_guests', 'bedrooms', 'bathrooms']
    ordering = ['price_per_night']
    search_fields = ['title', 'description', 'city__city']

class PropertyDetailAPIView(generics.RetrieveAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertyDetailSerializers

class PropertyCreateAPIView(generics.CreateAPIView):
    serializer_class = PropertyCreateSerializers

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    permission_classes = [permissions.IsAuthenticated, IsOwner]

class PropertyUpdateAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertyUpdateSerializers

    permission_classes = [permissions.IsAuthenticated, IsOwner]
    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

class BookingListAPIView(generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingListSerializers

class BookingCreateAPIView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializers

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)

    permission_classes = [permissions.IsAuthenticated, IsGuest]

class ReviewCreateAPIView(generics.CreateAPIView):
    serializer_class = ReviewCreateSerializers

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)

    permission_classes = [permissions.IsAuthenticated, IsGuest]

class FavoriteItemListAPIView(generics.ListAPIView):
    serializer_class = FavoriteItemListSerializer

    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return FavoriteItem.objects.filter(favorite__user=self.request.user)
