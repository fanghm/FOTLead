from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from .models import Issue, Comment
from .forms import IssueForm, CommentForm

# show issue form to create or update issue
def issue_form(request, pk=None):
    if pk:
        issue = get_object_or_404(Issue, pk=pk)
    else:
        issue = Issue()

    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            return redirect(reverse("tracker:issue_list"))
    else:
        form = IssueForm(instance=issue)

    return render(request, 'issue_form.html', {'form': form, 'issue': issue})

# show issue list grouped by type, and done issues
class IssueListView(generic.ListView):
    model = Issue
    template_name = 'issue_list.html'
    context_object_name = 'issues'
    ordering = ['type']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        issues = context['issues']
        grouped_issues = {}
        done_issues = []

        for issue in issues:
            if issue.status == 'closed' or issue.status == 'discarded':
                done_issues.append(issue)
            else:
                type = issue.get_type_display()
                if type not in grouped_issues:
                    grouped_issues[type] = []
                grouped_issues[type].append(issue)
        
        context['grouped_issues'] = grouped_issues
        context['done_issues'] = done_issues
        return context

# show issue detail, related comments and a new form to add comment and update issue status
def issue_detail(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    comments = issue.comments.all()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST, issue=issue)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user.username  # use the login user
            comment.issue = issue
            comment.save()
            return redirect(reverse("tracker:issue_detail", args=(issue.pk,)))
    else:
        comment_form = CommentForm(issue=issue)

    return render(request, 'issue_detail.html', {
        'issue': issue,
        'comments': comments,
        'comment_form': comment_form
    })
