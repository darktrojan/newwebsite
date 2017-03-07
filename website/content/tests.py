from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils.timezone import now

from content.models import Page


class PageTestCase(TestCase):
	def setUp(self):
		me = User.objects.create_superuser(username='me', email=None, password='me')
		for a in ['home', 'one', 'two']:
			Page.objects.create(
				alias=a,
				title='Test',
				content=a,
				modified=now(),
				modifier=me,
				status='P',
				template='test.html',
			)

	def test_tautology(self):
		one = Page.objects.get(alias='one')
		two = Page.objects.get(alias='two')
		self.assertEqual(one.content, 'one')
		self.assertEqual(two.content, 'two')

	def test_url(self):
		home = Page.objects.get(alias='home')
		one = Page.objects.get(alias='one')
		two = Page.objects.get(alias='two')
		self.assertEqual(home.get_absolute_url(), '/')
		self.assertEqual(one.get_absolute_url(), '/one')
		self.assertEqual(two.get_absolute_url(), '/two')

		two.parent = one
		two.save(update_fields=['parent'])
		self.assertEqual(two.get_absolute_url(), '/one/two')

		one.parent = home
		one.save(update_fields=['parent'])
		two.refresh_from_db()
		self.assertEqual(one.get_absolute_url(), '/one')
		self.assertEqual(two.get_absolute_url(), '/one/two')

	def _test_client(self, logged_in=False):
		client = Client()
		if logged_in:
			client.login(username='me', password='me')

		response = client.get('/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['title'], 'Test')
		self.assertEqual(response.context['content'], 'home')
		self.assertEqual(response.context['extra_header_content'], '')

		response = client.get('/one')
		self.assertEqual(response.status_code, 200)
		response = client.get('/two')
		self.assertEqual(response.status_code, 200)

		response = client.get('/three')
		self.assertEqual(response.status_code, 404)

		response = client.get('/four/two')
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], '/two')

		one = Page.objects.get(alias='one')
		for s in ['D', 'A']:
			one.status = s
			one.save()

			response = client.get('/one')
			self.assertEqual(response.status_code, 200 if logged_in else 404)

		two = Page.objects.get(alias='two')
		two.parent = one
		two.save(update_fields=['parent'])

		response = client.get('/two')
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], '/one/two')

		response = client.get('/four/two')
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], '/one/two')

	def test_client(self):
		self._test_client(True)

	def test_client_anon(self):
		self._test_client(False)

	def test_revisions(self):
		me = User.objects.get(username='me')
		one = Page.objects.get(alias='one')
		self.assertEqual(one.revisions.count(), 1)

		current_modified = one.modified

		first = one.revisions.first()
		self.assertEqual(first.title, one.title)
		self.assertEqual(first.content, one.content)
		self.assertEqual(first.extra_header_content, one.extra_header_content)
		self.assertTrue(abs(first.modified - current_modified) < timedelta(seconds=1))
		self.assertEqual(first.modifier, me)

		one.content = 'five!'
		one.save()

		first.refresh_from_db()
		second = one.revisions.last()
		self.assertEqual(second.title, one.title)
		self.assertEqual(second.content, one.content)
		self.assertNotEqual(second.content, first.content)
		self.assertEqual(second.extra_header_content, one.extra_header_content)
		self.assertNotEqual(second.modified, first.modified)
		# modified is not changed when working with Page objects directly
		self.assertEqual(one.modified, current_modified)
		self.assertEqual(second.modifier, me)
