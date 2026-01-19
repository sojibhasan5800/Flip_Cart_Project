# filters.py
import django_filters
from .models import Coupon
from django.utils import timezone

class CouponFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    min_discount = django_filters.NumberFilter(field_name='discount', lookup_expr='gte')
    max_discount = django_filters.NumberFilter(field_name='discount', lookup_expr='lte')
    expires_before = django_filters.DateTimeFilter(field_name='valid_to', lookup_expr='lte')
    expires_after = django_filters.DateTimeFilter(field_name='valid_to', lookup_expr='gte')
    is_expiring_soon = django_filters.BooleanFilter(method='filter_expiring_soon')
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'is_active', 'for_new_user', 
            'for_member', 'is_public'
        ]
    
    def filter_expiring_soon(self, queryset, name, value):
        if value:
            # Coupons expiring in next 7 days
            next_week = timezone.now() + timezone.timedelta(days=7)
            return queryset.filter(
                valid_to__lte=next_week,
                valid_to__gt=timezone.now(),
                is_active=True
            )
        return queryset