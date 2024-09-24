from django import forms
from django.db import transaction

from .models import Comment, Issue


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ["type", "title", "description", "status", "priority"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 107}),
            "description": forms.Textarea(attrs={"rows": 20, "cols": 100}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        issue = super().save(commit=False)
        if self.user:
            issue.author = self.user.username
        if commit:
            issue.save()
        return issue


class CommentForm(forms.ModelForm):
    """add a comment and update the issue's status and priority"""

    # all fields defined within form will be added to self.fields automatically
    new_status = forms.ChoiceField(
        choices=Issue.STATUS_CHOICES, required=False, label="Issue Status"
    )

    new_priority = forms.ChoiceField(
        choices=Issue.PRIORITY_LEVELS, required=False, label="Issue Priority"
    )

    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 10, "cols": 100}),
        }
        labels = {
            "text": "Comment",
        }

    def __init__(self, *args, **kwargs):
        self.issue = kwargs.pop("issue", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.issue:
            self.fields["new_status"].initial = self.issue.status
            self.fields["new_priority"].initial = self.issue.priority

    def clean(self):
        cleaned_data = super().clean()
        if not self.issue or not self.user:
            raise forms.ValidationError("User/Issue is mandatory")
        return cleaned_data

    @transaction.atomic
    def save(self):
        comment = super().save(False)
        comment.issue = self.issue
        comment.author = self.user.username
        comment.save()

        new_status = self.cleaned_data["new_status"]
        new_priority = self.cleaned_data["new_priority"]
        if new_status != self.issue.status or new_priority != self.issue.priority:
            self.issue.status = new_status
            self.issue.priority = new_priority
            self.issue.save()

        return comment
