# views.py
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, UpdateView

from .models import Feature, FeatureRoles
from .team_forms import FeatureRolesForm


class CreateFeatureRolesView(CreateView):
    model = FeatureRoles
    fields = ('pdm', 'apm', 'fot_lead', 'cfam_lead')
    # form_class = FeatureRolesForm
    template_name = 'fot/team_form.html'
    # success_url = reverse('fotd:fot_detail', args=(self.object.pk,))

    # handle foreign key only in form_valid()
    def form_valid(self, form):
        feature = get_object_or_404(Feature, id=self.object.pk)
        form.instance.feature = feature
        return super(CreateFeatureRolesView, self).form_valid(form)


# https://docs.djangoproject.com/en/dev/topics/class-based-views/generic-editing/#model-forms
class UpdateFeatureRolesView(UpdateView):
    model = FeatureRoles
    form_class = FeatureRolesForm
    template_name = 'fot/team_form.html'
    # success_url = reverse('fotd:fot_detail', args=(self.object.pk,))

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    # The default implementation for form_valid() simply redirects to the success_url
    def form_valid(self, form):
        feature = get_object_or_404(Feature, id=self.object.pk)
        form.instance.feature = feature
        return super(UpdateFeatureRolesView, self).form_valid(form)


# def fot_add(request, fid):
#     feature = get_object_or_404(Feature, id=fid)

#     # Get or create the FeatureRoles instance
#     feature_roles, created = FeatureRoles.objects.get_or_create(feature=feature)

#     # Create form instances
#     feature_roles_form = FeatureRolesForm(request.POST or None,
#       instance=feature_roles, feature=feature)
#     TeamMemberFormSet = modelformset_factory(TeamMember, form=TeamMemberForm, extra=1)
#     team_member_formset = TeamMemberFormSet(request.POST or None,
#       queryset=TeamMember.objects.filter(feature=feature),
#       form_kwargs={'feature': feature})

#     if request.method == 'POST':
#         if feature_roles_form.is_valid() and team_member_formset.is_valid():
#             feature_roles_form.save()
#             team_member_formset.save()
#             return redirect('success_url')  # Replace with your success URL

#     context = {
#         'fid': fid,
#         'feature_roles_form': feature_roles_form,
#         'team_member_formset': team_member_formset,
#     }
#     return render(request, 'fot/fot_add.html', context)
