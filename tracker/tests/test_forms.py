from django.test import TestCase

from tracker.forms import CommentForm, IssueForm
from tracker.models import Issue


class IssueFormTest(TestCase):

    def test_issue_form_valid_data(self):
        form = IssueForm(
            data={
                "type": "bug",
                "title": "Test Issue",
                "description": "This is a test issue.",
                "status": "open",
                "priority": "critical",
            }
        )
        self.assertTrue(form.is_valid())

    def test_issue_form_invalid_data(self):
        form = IssueForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)  # 4 fields are mandatory


class CommentFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.issue = Issue.objects.create(
            title="Test Issue",
            description="This is a test issue.",
            type="bug",
            status="open",
            priority="high",
        )

    def test_comment_form_valid_data(self):
        form = CommentForm(
            data={
                "author": "Test Author",
                "text": "This is a test comment.",
                "new_status": "closed",
            },
            issue=self.issue,
        )
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_data(self):
        form = CommentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)  # 'text' and Issue are mandatory

    def test_comment_form_save(self):
        form = CommentForm(
            data={
                "author": "Test Author",
                "text": "This is a test comment.",
                "new_status": "closed",
            },
            issue=self.issue,
        )

        self.assertTrue(form.is_valid())
        comment = form.save()

        self.assertEqual(comment.text, "This is a test comment.")
        self.assertEqual(comment.author, "Test Author")
        self.assertEqual(comment.issue, self.issue)
        self.assertEqual(self.issue.status, "closed")

    def test_comment_form_save_without_issue(self):
        form = CommentForm(
            data={
                "author": "Test Author",
                "text": "This is a test comment.",
                "new_status": "closed",
            }
        )
        self.assertFalse(form.is_valid())
