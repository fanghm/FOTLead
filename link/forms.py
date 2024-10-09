from django import forms

from .models import Link


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ["name", "url", "type", "domain", "description"]
        widgets = {
            "type": forms.RadioSelect,
            "url": forms.TextInput(attrs={"size": 80}),
            "description": forms.Textarea(attrs={"rows": 5, "cols": 70}),
        }
