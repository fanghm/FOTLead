from django import forms

# from django_select2 import forms as s2forms
from .models import Link


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ["name", "url", "type", "domain", "tags", "description"]
        widgets = {
            "type": forms.RadioSelect,
            "url": forms.TextInput(attrs={"size": 80}),
            "description": forms.Textarea(attrs={"rows": 5, "cols": 70}),
            # "tags": s2forms.ModelSelect2TagWidget(
            #     model=Tag,
            #     search_fields=['name__icontains'],
            #     attrs={
            #         'data-tags': 'true',
            #         'data-token-separators': '[",", " "]',
            #         'style': 'width: 400px;',
            #     }
            # )
        }
