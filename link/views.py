from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LinkForm
from .models import Link


def link_list(request):
    links = Link.objects.all()
    return render(request, "link_list.html", {"links": links})


def link_add(request):
    if request.method == "POST":
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.submitted_by = request.user
            link.save()
            return redirect("link_list")
    else:
        form = LinkForm()
    return render(request, "link_form.html", {"form": form})


def link_edit(request, pk):
    link = get_object_or_404(Link, pk=pk)
    if request.method == "POST":
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            return redirect("link_list")
    else:
        form = LinkForm(instance=link)
    return render(request, "link_edit.html", {"form": form})


def link_approve(request, pk):
    link = get_object_or_404(Link, pk=pk)
    if request.method == "POST":
        link.status = "approved"
        link.approved_by = request.user
        link.approved_at = timezone.now()
        link.save()
        return redirect("link_list")
    return render(request, "link_approve.html", {"link": link})
