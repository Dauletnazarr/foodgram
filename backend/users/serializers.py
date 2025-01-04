from drf_extra_fields.fields import Base64ImageField

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import OwnUser, Subscription


class OwnUserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = OwnUser
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = OwnUser(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class OwnUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = OwnUser
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar']


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if len(value) < 8:  # Пример проверки: минимальная длина пароля
            raise serializers.ValidationError(
                "Пароль должен содержать не менее 8 символов.")
        return value

    def save(self, user):
        if not user.check_password(self.validated_data['current_password']):
            raise serializers.ValidationError("Текущий пароль неверен.")

        user.set_password(self.validated_data['new_password'])
        user.save()


class AvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = OwnUser
        fields = ['avatar']

    def update(self, instance, validated_data):
        # Base64ImageField автоматически обрабатывает изображение
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    subscribed_to = serializers.SlugRelatedField(
        slug_field='username',
        queryset=OwnUser.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('user', 'subscribed_to')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'subscribed_to']
            )
        ]
