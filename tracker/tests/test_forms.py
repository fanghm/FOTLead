from django.test import TestCase
from tracker.forms import IssueForm, CommentForm
from tracker.models import Issue, Comment

class IssueFormTest(TestCase):

    def test_issue_form_valid_data(self):
        form = IssueForm(data={
            'type': 'bug',
            'title': 'Test Issue',
            'description': 'This is a test issue.',
            'status': 'open'
        })
        self.assertTrue(form.is_valid())

    def test_issue_form_invalid_data(self):
        form = IssueForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)  # 3 fields are required, except 'description'

class CommentFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.issue = Issue.objects.create(
            title="Test Issue",
            description="This is a test issue.",
            type="bug",
            status="open"
        )

    def test_comment_form_valid_data(self):
        form = CommentForm(data={
            'author': 'Test Author',
            'text': 'This is a test comment.',
            'new_issue_status': 'closed'
        }, issue=self.issue)
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_data(self):
        form = CommentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertGreaterEqual(len(form.errors), 1)  # 'text' and Issue field is required

    def test_comment_form_save(self):
        form = CommentForm(data={
            'author': 'Test Author',
            'text': 'This is a test comment.',
            'new_issue_status': 'closed'
        }, issue=self.issue)
        self.assertTrue(form.is_valid())
        comment = form.save()
        self.assertEqual(comment.text, 'This is a test comment.')
        self.assertEqual(comment.author, 'Test Author')
        self.assertEqual(comment.issue, self.issue)
        self.assertEqual(self.issue.status, 'closed')

    def test_comment_form_save_without_issue(self):
        form = CommentForm(data={
            'author': 'Test Author',
            'text': 'This is a test comment.',
            'new_issue_status': 'closed'
        })
        self.assertFalse(form.is_valid())