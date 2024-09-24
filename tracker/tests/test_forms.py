from django.contrib.auth.models import User
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

        # 5 fields are mandatory, but author is not included in the form
        self.assertEqual(len(form.errors), 4)


class CommentFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="comment user", password="Test1Pwd!"
        )
        cls.issue = Issue.objects.create(
            title="Test Issue",
            description="This is a test issue.",
            type="bug",
            status="open",
            priority="medium",
            author="issue author",
        )

    def test_comment_form_valid_data(self):
        form = CommentForm(
            data={
                "text": "This is a test comment.",
            },
            issue=self.issue,
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_data(self):
        form = CommentForm(data={})
        self.assertFalse(form.is_valid())
        # print(form.errors)
        self.assertEqual(len(form.errors), 2)  # 'text' and User/Issue are mandatory

    def test_comment_form_save(self):
        form = CommentForm(
            data={
                "text": "This is a test comment.",
                "new_status": "closed",
                "new_priority": "high",
            },
            issue=self.issue,
            user=self.user,
        )

        self.assertTrue(form.is_valid())
        comment = form.save()

        self.assertEqual(comment.text, "This is a test comment.")
        self.assertEqual(comment.author, "comment user")
        self.assertEqual(comment.issue, self.issue)
        self.assertEqual(self.issue.status, "closed")
        self.assertEqual(self.issue.priority, "high")
