from rest_framework import serializers
from merchant_user.models import Organization
from store.models import ReviewRating


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """
    Organization(Store) creation serializer
    Used when a merchant submits store application
    """

    class Meta:
        model = Organization
        fields = [
            "store_logo",
            "username",
            "business_name",
            "store_description",
            "business_email",
            "phone",
            "address_line1",
        ]

    def create(self, validated_data):
        """
        Create organization in pending/unverified state
        """
        print("data", validated_data)
        organization = Organization.objects.create(
            **validated_data,
            is_verified=False,
            is_active=True,
            subscription_status="inactive",
            is_trial=True,
        )
        return organization



class BasicStoreInfoSerializer(serializers.ModelSerializer):
    """
    Minimal store information shown in seller dashboard / navbar
    """
    class Meta:
        model = Organization
        fields = [
            'id',
            'username',
            'business_name',
            'store_logo',
            'store_description',
            'business_email',
            'phone',
            'is_verified',
            'is_active',
            'subscription_status',
            'is_trial',
            'days_remaining_in_trial',   # if you want to show trial countdown
        ]
        read_only_fields = fields


class ReviewUserSerializer(serializers.Serializer):
    name = serializers.CharField(source='user.full_name')
    image = serializers.CharField(source='user.profile_picture.url', allow_null=True)


class ReviewProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source='product_name')
    category = serializers.CharField(source='category.category_name')


class ReviewSerializer(serializers.ModelSerializer):
    user = ReviewUserSerializer(read_only=True)
    product = ReviewProductSerializer(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ReviewRating
        fields = ['id', 'user', 'product', 'rating', 'review', 'createdAt', 'subject']


class SellerDashboardSerializer(serializers.Serializer):
    totalProducts = serializers.IntegerField()
    totalEarnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    totalOrders = serializers.IntegerField()
    ratings = ReviewSerializer(many=True)