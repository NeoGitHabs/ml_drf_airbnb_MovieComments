# AirBNB_Comments_drf/my_app/serializers.py

from rest_framework import serializers
from .models import UserProfile, City, Property, Images, Booking, Review, Favorite, FavoriteItem, Amenity
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
import joblib
import os


# ── Загрузка ML-артефактов один раз при старте ────────────────────────────────
def _load_ml():
    model = joblib.load(os.path.join(settings.BASE_DIR, 'model_nb_airbnb_comments.pkl'))
    vector = joblib.load(os.path.join(settings.BASE_DIR, 'vector_airbnb_comments.pkl'))
    return model, vector

_nb_model, _nb_vector = _load_ml()


# ── Auth ───────────────────────────────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return UserProfile.objects.create_user(**validated_data)

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {'username': instance.username, 'email': instance.email},
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Неверные учетные данные")

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {'username': instance.username, 'email': instance.email},
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


# ── Профиль ────────────────────────────────────────────────────────────────────
class UserProfileSerializers(serializers.ModelSerializer):
    account_created_date = serializers.DateTimeField(format='%d-%m-%Y %H:%M')

    class Meta:
        model = UserProfile
        fields = ['id', 'avatar', 'first_name', 'last_name', 'username',
                  'email', 'password', 'phone_number', 'role', 'account_created_date']
        extra_kwargs = {'password': {'write_only': True}}


class UserProfileUpdateSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'first_name', 'last_name', 'username',
                  'email', 'password', 'phone_number', 'role']
        extra_kwargs = {'password': {'write_only': True}}


class UserProfilePublicDateSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'first_name', 'last_name', 'email', 'phone_number']


# ── Недвижимость ───────────────────────────────────────────────────────────────
class CitySerializers(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'city']


class ImageSerializers(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ['image']


class AmenitySerializers(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name_amenity', 'icon_amenity']


class PropertySerializers(serializers.ModelSerializer):
    city = CitySerializers(read_only=True)
    images = ImageSerializers(many=True, read_only=True, source='images_set')
    count_reviews = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ['id', 'title', 'city', 'price_per_night', 'images',
                  'is_active', 'count_reviews', 'avg_rating']

    def get_avg_rating(self, obj):
        return obj.get_avg_rating()

    def get_count_reviews(self, obj):
        return obj.get_count_reviews()


# ── Отзывы ─────────────────────────────────────────────────────────────────────
class ReviewListSerializers(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%d-%m-%Y %H:%M')
    guest = UserProfilePublicDateSerializers(read_only=True)
    property = PropertySerializers(read_only=True)
    sentiment = serializers.SerializerMethodField()  # переименовано: понятнее

    class Meta:
        model = Review
        fields = ['id', 'guest', 'property', 'rating', 'comment', 'sentiment', 'created_at']

    def get_sentiment(self, obj):
        # возвращаем строку, а не numpy-массив
        return str(_nb_model.predict(_nb_vector.transform([obj.comment]))[0])


class ReviewCreateSerializers(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['property', 'rating', 'comment']


# ── Детали и CRUD недвижимости ─────────────────────────────────────────────────
class PropertyDetailSerializers(serializers.ModelSerializer):
    owner = UserProfilePublicDateSerializers(read_only=True)
    city = CitySerializers(read_only=True)
    images = ImageSerializers(many=True, read_only=True, source='images_set')
    amenities = AmenitySerializers(read_only=True, many=True, source='amenity_set')
    reviews = ReviewListSerializers(read_only=True, many=True)
    count_reviews = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ['id', 'images', 'owner', 'title', 'description', 'price_per_night',
                  'city', 'address', 'property_type', 'rules', 'amenities',
                  'max_guests', 'bedrooms', 'bathrooms', 'is_active',
                  'reviews', 'count_reviews', 'avg_rating']

    def get_avg_rating(self, obj):
        return obj.get_avg_rating()

    def get_count_reviews(self, obj):
        return obj.get_count_reviews()


class PropertyUpdateSerializers(serializers.ModelSerializer):
    owner = UserProfilePublicDateSerializers(read_only=True)
    city = CitySerializers(read_only=True)
    images = ImageSerializers(many=True, read_only=True, source='images_set')

    class Meta:
        model = Property
        fields = ['images', 'owner', 'title', 'description', 'price_per_night',
                  'city', 'address', 'property_type', 'rules',
                  'max_guests', 'bedrooms', 'bathrooms', 'is_active']


class PropertyCreateSerializers(serializers.ModelSerializer):
    owner = UserProfilePublicDateSerializers(read_only=True)
    city = CitySerializers(read_only=True)
    images = ImageSerializers(many=True, read_only=True, source='images_set')

    class Meta:
        model = Property
        fields = ['images', 'owner', 'title', 'description', 'price_per_night',
                  'city', 'address', 'property_type', 'rules',
                  'max_guests', 'bedrooms', 'bathrooms', 'is_active']


# ── Бронирование ───────────────────────────────────────────────────────────────
class BookingListSerializers(serializers.ModelSerializer):
    guest = UserProfileSerializers(read_only=True)
    property = PropertySerializers(read_only=True)
    created_at = serializers.DateTimeField(format='%d-%m-%Y %H:%M')
    check_in = serializers.DateTimeField(format='%d-%m-%Y %H:%M')
    check_out = serializers.DateTimeField(format='%d-%m-%Y %H:%M')

    class Meta:
        model = Booking
        fields = ['id', 'guest', 'property', 'check_in', 'check_out', 'status', 'created_at']


class BookingCreateSerializers(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['property', 'check_in', 'check_out']


# ── Избранное ──────────────────────────────────────────────────────────────────
class FavoriteItemListSerializer(serializers.ModelSerializer):
    user = UserProfilePublicDateSerializers(source='favorite.user', read_only=True)
    property = PropertySerializers(read_only=True)

    class Meta:
        model = FavoriteItem
        fields = ['id', 'user', 'property']