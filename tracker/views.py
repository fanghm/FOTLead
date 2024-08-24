from django.shortcuts import render, get_object_or_404, redirect
from .models import Issue, Comment
from .forms import IssueForm, CommentForm

def issue_form(request, pk=None):
    if pk:
        issue = get_object_or_404(Issue, pk=pk)
    else:
        issue = Issue()

    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            return redirect('issue_list')
    else:
        form = IssueForm(instance=issue)

    return render(request, 'issue_form.html', {'form': form, 'issue': issue})

def issue_list(request):
    issues = Issue.objects.all().order_by('type')
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
    
    return render(request, 'issue_list.html', {
        'grouped_issues': grouped_issues,
        'done_issues': done_issues
        })

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
            return redirect('issue_detail', pk=issue.pk)
    else:
        comment_form = CommentForm(issue=issue)

    return render(request, 'issue_detail.html', {
        'issue': issue,
        'comments': comments,
        'comment_form': comment_form
    })

def issue_create(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save()
            return redirect('issue_detail', pk=issue.pk)
    else:
        form = IssueForm()
    return render(request, 'issue_form.html', {'form': form})

def issue_update(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            return redirect('issue_list')
    else:
        form = IssueForm(instance=issue)

    return render(request, 'issue_form.html', {'form': form, 'issue': issue})