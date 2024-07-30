from django import forms
from .models import Issue, Comment

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['issue_type', 'title', 'description', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'size': 100}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 80}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['author', 'text']
        widgets = {
            'author': forms.HiddenInput(),
        }
        labels = {
            'text': 'Comment',
        }