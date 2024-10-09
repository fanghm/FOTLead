from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from link.models import Link


class LinkViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpwd')
        self.client.login(username='testuser', password='testpwd')
        self.link1 = Link.objects.create(
            name='Google',
            url='http://google.com',
            type='tool',
            description='Search Engine',
            status='approved',
            domain='google.com',
        )
        self.link2 = Link.objects.create(
            name='ChatGPT',
            url='https://chatgpt.com',
            type='tool',
            description='AI Service',
            status='pending',
            domain='chatgpt.com',
        )
        self.link3 = Link.objects.create(
            name='GitHub',
            url='http://github.com',
            type='tool',
            description='Code Hosting',
            status='approved',
            domain='github.com',
        )

    def test_link_admin(self):
        response = self.client.get(reverse('link:link_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'link_admin.html')
        self.assertIn('grouped_links', response.context)
        self.assertIn('approved', response.context['grouped_links'])
        self.assertIn('pending', response.context['grouped_links'])

    def test_link_list(self):
        response = self.client.get(reverse('link:link_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'link_list.html')
        self.assertIn('grouped_links', response.context)

        grouped_links = response.context['grouped_links']
        self.assertTrue(any('chatgpt.com' in group for group in grouped_links))

    def test_link_list_with_letter(self):
        response = self.client.get(reverse('link:link_list'), {'index': 'G'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'link_list.html')
        self.assertIn('grouped_links', response.context)

        grouped_links = response.context['grouped_links']
        self.assertTrue(any('google.com' in group for group in grouped_links))
        self.assertTrue(any('github.com' in group for group in grouped_links))

    def test_link_edit_get(self):
        response = self.client.get(reverse('link:link_edit', args=[self.link1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'link_edit.html')
        self.assertContains(response, self.link1.name)

    def test_link_edit_post_approve(self):
        response = self.client.post(
            reverse('link:link_edit', args=[self.link2.pk]),
            {
                'action': 'approve',
                'name': self.link2.name,
                'url': self.link2.url,
                'type': self.link2.type,
                'domain': self.link2.domain,
                'description': self.link2.description + ' (Approved)',
            },
        )
        self.assertRedirects(response, reverse('link:link_admin'))
        self.link2.refresh_from_db()
        self.assertEqual(self.link2.status, 'approved')
        self.assertEqual(self.link2.approved_by, self.user)
        self.assertNotEqual(self.link2.description, 'AI Service')

    def test_link_edit_post_reject(self):
        response = self.client.post(
            reverse('link:link_edit', args=[self.link2.pk]),
            {
                'action': 'reject',
                'name': self.link2.name,
                'url': self.link2.url,
                'type': self.link2.type,
                'domain': self.link2.domain,
                'description': self.link2.description + ' (Rejected)',
            },
        )
        self.assertRedirects(response, reverse('link:link_admin'))
        self.link2.refresh_from_db()
        self.assertEqual(self.link2.status, 'rejected')
        self.assertEqual(self.link2.approved_by, self.user)
        self.assertNotEqual(self.link2.description, 'AI Service')

    def test_link_edit_post_save(self):
        new_name = 'Updated Test Link'
        response = self.client.post(
            reverse('link:link_edit', args=[self.link1.pk]),
            {
                'name': new_name,
                'url': self.link1.url,
                'type': self.link2.type,
                'domain': self.link2.domain,
                'description': self.link1.description,
            },
        )
        self.assertRedirects(response, reverse('link:link_admin'))
        self.link1.refresh_from_db()
        self.assertEqual(self.link1.name, new_name)
