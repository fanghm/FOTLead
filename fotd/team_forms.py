# fot_forms.py
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django import forms

from .models import FeatureRoles, TeamMember


class FeatureRolesForm(forms.ModelForm):
    class Meta:
        model = FeatureRoles
        fields = ['pdm', 'apm', 'fot_lead', 'cfam_lead', 'lese', 'ftl', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 1, 'cols': 80}),
        }

    def __init__(self, *args, **kwargs):
        self.feature = kwargs.pop('feature', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # self.helper.add_input(Submit('submit', 'Save person'))

        self.helper.layout = Layout(
            Row(
                Column('fot_lead', css_class='form-group col-md-4 mb-0'),
                Column('pdm', css_class='form-group col-md-4 mb-0'),
                Column('apm', css_class='form-group col-md-4 mb-0'),
                css_class='form-row',
            ),
            Row(
                Column('cfam_lead', css_class='form-group col-md-4 mb-0'),
                Column('lese', css_class='form-group col-md-4 mb-0'),
                Column('ftl', css_class='form-group col-md-4 mb-0'),
                css_class='form-row',
            ),
            'comment',
            Submit('submit', 'Save'),
        )

    # def clean(self):
    #     cleaned_data = super().clean()
    #     if not self.feature:
    #         raise forms.ValidationError('Feature is mandatory')
    #     return cleaned_data

    def save(self, commit=True):
        roles = super().save(commit=False)
        if self.feature:
            roles.feature = self.feature

        if commit:
            roles.save()
        return roles


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['team', 'apo', 'role', 'name', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 1, 'cols': 80}),
        }

    def __init__(self, *args, **kwargs):
        self.feature = kwargs.pop('feature', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.feature:
            raise forms.ValidationError('Feature is mandatory')
        return cleaned_data

    def save(self, commit=True):
        roles = super().save(commit=False)
        if self.feature:
            roles.feature = self.feature

        if commit:
            roles.save()
        return roles
