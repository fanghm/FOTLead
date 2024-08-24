from django.test import TestCase
from tracker.models import Issue, Comment

class IssueModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.issue = Issue.objects.create(
            title="Test Issue",
            description="This is a test issue.",
            type="bug",
            status="open"
        )

    def test_issue_creation(self):
        self.assertEqual(self.issue.title, "Test Issue")
        self.assertEqual(self.issue.description, "This is a test issue.")
        self.assertEqual(self.issue.type, "bug")
        self.assertEqual(self.issue.status, "open")
        self.assertIsNotNone(self.issue.created_at)
        self.assertIsNotNone(self.issue.updated_at)

    def test_issue_str(self):
        self.assertEqual(str(self.issue), "Test Issue")

class CommentModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.issue = Issue.objects.create(
            title="Test Issue",
            description="This is a test issue.",
            type="bug",
            status="open"
        )
        cls.comment = Comment.objects.create(
            issue=cls.issue,
            author="Test Author",
            text="This is a test comment."
        )

    def test_comment_creation(self):
        self.assertEqual(self.comment.issue, self.issue)
        self.assertEqual(self.comment.author, "Test Author")
        self.assertEqual(self.comment.text, "This is a test comment.")
        self.assertIsNotNone(self.comment.created_at)

    def test_comment_str(self):
        self.assertEqual(str(self.comment), "This is a test comme")