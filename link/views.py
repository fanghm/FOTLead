from collections import defaultdict

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import LinkForm
from .models import Link


def link_admin(request):
    links = Link.objects.order_by("status")
    grouped_links = {}
    for link in links:
        if link.status not in grouped_links:
            grouped_links[link.status] = []
        grouped_links[link.status].append(link)
    return render(request, "link_admin.html", {"grouped_links": grouped_links})


def link_list(request):
    links = Link.objects.filter(status="approved")

    domain_initials = sorted(set(link.domain[0].upper() for link in links))
    selected_initial = request.GET.get(
        'index', domain_initials[0] if domain_initials else ''
    )

    grouped_links = defaultdict(list)
    for link in links:
        if not selected_initial or link.domain[0].upper() == selected_initial:
            grouped_links[link.domain].append(link)

    grouped_links = list(grouped_links.items())
    # print(f'grouped_links: {grouped_links}')

    return render(
        request,
        'link_list.html',
        {
            'grouped_links': grouped_links,
            'domain_initials': domain_initials,
            'selected_initial': selected_initial,
        },
    )


def link_add(request):
    if request.method == "POST":
        form = LinkForm(request.POST)
        # print(f'INIT form: {form}')
        if form.is_valid():
            link = form.save(commit=False)
            link.submitted_by = request.user
            print(f'VALID link: {link}')
            link.save()
            return redirect(reverse("link:link_admin"))
    else:
        form = LinkForm()
    return render(request, "link_form.html", {"form": form})


def link_edit(request, pk):
    link = get_object_or_404(Link, pk=pk)
    if request.method == "POST":
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            link = form.save(commit=False)
            action = request.POST.get('action')
            if action == 'approve':
                link.status = 'approved'
                link.approved_by = request.user
                link.approved_at = timezone.now()
            elif action == 'reject':
                link.status = 'rejected'
                link.approved_by = request.user
                link.approved_at = timezone.now()
            link.save()
            return redirect(reverse('link:link_admin'))
        else:
            print(f'Invalid form: {form.errors}')
    else:
        form = LinkForm(instance=link)
    return render(request, "link_edit.html", {"form": form, 'link': link})


def link_search(request):
    query = request.GET.get('q', '')

    if query:
        search_results = (
            Link.objects.filter(
                Q(name__icontains=query)
                | Q(url__icontains=query)
                | Q(domain__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(description__icontains=query)
            )
            .filter(status="approved")
            .distinct()
        )
    else:
        search_results = Link.objects.none()

    results = [{'name': link.name, 'url': link.url} for link in search_results]
    return JsonResponse({'search_results': results, 'query': query})
