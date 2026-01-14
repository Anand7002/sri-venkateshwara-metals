from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='userrole'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User role'
        verbose_name_plural = 'User roles'

    def __str__(self):
        return f'{self.user.username} → {self.get_role_display()}'

