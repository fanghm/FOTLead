from django import forms

from .models import Comment, Issue


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ["author", "type", "title", "description", "status", "priority"]
        widgets = {
            "author": forms.HiddenInput(),
            "title": forms.TextInput(attrs={"size": 107}),
            "description": forms.Textarea(attrs={"rows": 20, "cols": 100}),
        }


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
        fields = ["author", "text"]
        widgets = {
            "author": forms.HiddenInput(),
            "text": forms.Textarea(attrs={"rows": 10, "cols": 100}),
        }
        labels = {
            "text": "Comment",
        }

    def __init__(self, *args, **kwargs):
        self.issue = kwargs.pop("issue", None)
        super().__init__(*args, **kwargs)
        if self.issue:
            self.fields["new_status"].initial = self.issue.status
            self.fields["new_priority"].initial = self.issue.priority

    def clean(self):
        cleaned_data = super().clean()
        if not self.issue:
            raise forms.ValidationError("Issue is mandatory")
        return cleaned_data

    def save(self, commit=True):
        comment = super().save(commit=False)
        new_status = self.cleaned_data["new_status"]
        new_priority = self.cleaned_data["new_priority"]

        if self.issue:
            comment.issue = self.issue

            if new_status != self.issue.status or new_priority != self.issue.priority:
                self.issue.status = new_status
                self.issue.priority = new_priority
                self.issue.save()

        if commit:
            comment.save()

        return comment
