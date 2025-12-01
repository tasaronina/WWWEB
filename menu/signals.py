from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance: User, created, **kwargs):
    # создаём профиль при создании пользователя
    if created:
        Profile.objects.create(user=instance, role="ADMIN" if instance.is_staff or instance.is_superuser else "USER")
    else:
        # при каждом сохранении пользователя убеждаемся что профиль существует
        Profile.objects.get_or_create(user=instance)
