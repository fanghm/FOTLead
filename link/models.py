from django.contrib.auth.models import User
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Link(models.Model):
    TYPE_CHOICES = [
        ("process", "Process"),
        ("tool", "Tool"),
        ("document", "Document"),
        ("contact", "Contact"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    name = models.CharField(max_length=200)
    url = models.URLField()
    type = models.CharField(max_length=25, choices=TYPE_CHOICES, default="other")
    domain = models.CharField(max_length=100)
    tags = models.ManyToManyField(Tag, blank=True, default=None)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    description = models.TextField(blank=True)

    submitted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    submitted_at = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_links",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
