from django.db import models
from django.urls import reverse


class Issue(models.Model):
    ISSUE_TYPES = [
        ("bug", "Bug"),
        ("improvement", "Improvement"),
        ("idea", "Idea"),
        ("feature", "Feature"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("discarded", "Discarded"),
        ("closed", "Closed"),
    ]

    PRIORITY_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=ISSUE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    priority = models.CharField(max_length=9, choices=PRIORITY_LEVELS, default="medium")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tracker:issue_detail", kwargs={"pk": self.pk})

    def is_high_priority(self):
        return self.priority in ["high", "critical"]


class Comment(models.Model):
    issue = models.ForeignKey(Issue, related_name="comments", on_delete=models.CASCADE)
    author = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:20]
