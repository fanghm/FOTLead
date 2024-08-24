from django import forms
from .models import Issue, Comment

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['type', 'title', 'description', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'size': 100}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 80}),
        }

class CommentForm(forms.ModelForm):
    new_issue_status = forms.ChoiceField(
        choices=Issue.STATUS_CHOICES, 
        required=False, 
        label='Issue Status'
    )

    class Meta:
        model = Comment
        fields = ['author', 'text']
        widgets = {
            'author': forms.HiddenInput(),
        }
        labels = {
            'text': 'Comment',
        }

    def __init__(self, *args, **kwargs):
        self.issue = kwargs.pop('issue', None)
        super().__init__(*args, **kwargs)
        if self.issue:
            self.fields['new_issue_status'].initial = self.issue.status

    def clean(self):
        cleaned_data = super().clean()
        if not self.issue:
            raise forms.ValidationError('Issue is mandatory')
        return cleaned_data

    def save(self, commit=True):
        comment = super().save(commit=False)
        if self.issue:
            comment.issue = self.issue
            if self.cleaned_data['new_issue_status']:
                self.issue.status = self.cleaned_data['new_issue_status']
                self.issue.save()

        if commit:
            comment.save()
        return comment