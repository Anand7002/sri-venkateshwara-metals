from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import UserRole

User = get_user_model()


def get_role_for_user(user):
    if hasattr(user, 'userrole'):
        return user.userrole.role
    return 'cashier'


class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email', 'role']

    def get_full_name(self, obj):
        full_name = obj.get_full_name()
        return full_name or obj.username

    def get_role(self, obj):
        return get_role_for_user(obj)


class UserManagementSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserRole.ROLE_CHOICES, write_only=True, required=False)
    password = serializers.CharField(write_only=True, min_length=6, required=False)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'password',
            'role',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def get_full_name(self, obj):
        full_name = obj.get_full_name()
        return full_name or obj.username

    def create(self, validated_data):
        role = validated_data.pop('role', 'cashier')
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        UserRole.objects.update_or_create(user=user, defaults={'role': role})
        return user

    def update(self, instance, validated_data):
        role = validated_data.pop('role', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if role:
            UserRole.objects.update_or_create(user=instance, defaults={'role': role})
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['role'] = get_role_for_user(instance)
        return data

