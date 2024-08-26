from django.test import TestCase, Client
from django.urls import reverse
from tracker.models import Issue, Comment
from django.contrib.auth.models import User
from tracker.forms import IssueForm, CommentForm

class IssueFormViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.issue = Issue.objects.create(title="Test Issue", description="Test Description", type="bug")

    def test_issue_create(self):
        response = self.client.get(reverse('tracker:issue_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'issue_form.html')
        self.assertIsInstance(response.context['form'], IssueForm)

    def test_issue_edit(self):
        response = self.client.get(reverse('tracker:issue_edit', args=[self.issue.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'issue_form.html')
        self.assertIsInstance(response.context['form'], IssueForm)
        self.assertIsInstance(response.context['issue'], Issue)

    def test_issue_form_post(self):
        data = {
            'type': 'bug',
            'title': 'Updated Issue',
            'description': 'Updated Description',
            'status': 'closed',
        }
        response = self.client.post(reverse('tracker:issue_edit', args=[self.issue.pk]), data)
        if response.status_code != 302:
            print(response.content)

        self.assertEqual(response.status_code, 302)
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.title, 'Updated Issue')
        self.assertEqual(self.issue.description, 'Updated Description')
        self.assertEqual(self.issue.status, 'closed')

class IssueListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.issue1 = Issue.objects.create(title="Issue 1", description="Description 1", type="bug")
        self.issue2 = Issue.objects.create(title="Issue 2", description="Description 2", type="feature", status="closed")
        self.issue1 = Issue.objects.create(title="Issue 3", description="Description 1", type="idea")
        self.issue2 = Issue.objects.create(title="Issue 4", description="Description 2", type="idea", status="discarded")
        self.issue1 = Issue.objects.create(title="Issue 3", description="Description 1", type="improvement")

    def test_issue_list_view(self):
        response = self.client.get(reverse('tracker:issue_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'issue_list.html')
        self.assertIn('grouped_issues', response.context)
        self.assertIn('done_issues', response.context)
        self.assertEqual(len(response.context['grouped_issues']), 3)
        self.assertEqual(len(response.context['done_issues']), 2)

class IssueDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.issue = Issue.objects.create(title="Test Issue", description="Test Description", type="bug", status='in_progress')
        self.comment = Comment.objects.create(issue=self.issue, author="testuser", text="Test Comment")

    def test_issue_detail_get(self):
        response = self.client.get(reverse('tracker:issue_detail', args=[self.issue.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'issue_detail.html')
        self.assertIn('issue', response.context)
        self.assertIn('comments', response.context)
        self.assertIn('comment_form', response.context)
        self.assertIsInstance(response.context['comment_form'], CommentForm)
        self.assertEqual(response.context['comment_form'].fields['new_issue_status'].initial, self.issue.status)

    def test_issue_detail_post(self):
        self.client.login(username='testuser', password='testpassword')
        data = {
            'text': 'New Comment',
        }
        response = self.client.post(reverse('tracker:issue_detail', args=[self.issue.pk]), data)
        self.assertEqual(response.status_code, 302) #redirect
        self.assertEqual(Comment.objects.count(), 2)
        new_comment = Comment.objects.latest('created_at')

        print(f'Comment: {new_comment.text} by {new_comment.author}')
        self.assertEqual(new_comment.text, data['text'])
        self.assertEqual(new_comment.issue, self.issue)
        self.assertEqual(new_comment.author, 'testuser')