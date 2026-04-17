from rest_framework import serializers
from .models import Link
from django.utils import timezone


class LinkSerializer(serializers.ModelSerializer):
    active_code = serializers.ReadOnlyField()
    short_url = serializers.SerializerMethodField()
    total_clicks = serializers.SerializerMethodField()

    class Meta:
        model = Link
        fields = [
            'id',
            'original_url',
            'short_code',
            'custom_alias',
            'active_code',
            'short_url',
            'password',
            'expires_at',
            'is_active',
            'created_at',
            'total_clicks',
        ]
        read_only_fields = ['short_code', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_short_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/{obj.active_code}/')
        return f'/{obj.active_code}/'

    # def get_total_clicks(self, obj):
    #     return obj.clicks.count()

    def validate_custom_alias(self, value):
        if value and Link.objects.filter(custom_alias=value).exists():
            raise serializers.ValidationError('This alias is already taken')
        return value

    def validate_expires_at(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError('Expiry date must be in the future')
        return value