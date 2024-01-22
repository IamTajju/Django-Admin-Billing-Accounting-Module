from django.db import models
from django.contrib.auth.models import User
# Create your models here.

role = [
    ('E', 'Editor'),
    ('P', 'Photographer'),
    ('C', 'Cinematographer'),
    ('A', 'Admin'),
]


class TeamMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=role)
    payment_per_event = models.IntegerField(default=0)

    def __str__(self):
        return self.user.get_full_name()
