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


class VersioningTestCase(TestCase):
	def setUp(self):
		self.me = User.objects.create_superuser(username='me', email=None, password='me')
		self.client = Client()
		self.client.login(username='me', password='me')

	def test_add_form(self):
		response = self.client.get('/admin/content/page/add/')
		self.assertEqual(response.context['original'], None)
		self.assertTrue('revision' not in response.context)
		self.assertContains(
			response, '<input type="submit" name="_newdraft" value="Save draft" class="default"/>', html=True
		)
		self.assertContains(
			response, '<input type="submit" name="_continue" value="Publish"/>', html=True
		)

	def test_create_publish(self):
		response = self.client.post('/admin/content/page/add/', data={
			'title': 'test',
			'alias': 'test',
			'parent': '',
			'template': 'test.html',
			'content': '<p>This is a test</p>',
			'extra_header_content': '',
			'_continue': 'Publish',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/')

		created = Page.objects.get(pk=1)
		self.assertEqual(created.status, 'P')
		self.assertEqual(created.revisions.count(), 1)

		revision = created.revisions.first()
		self.assertEqual(revision.type, 'H')

	def test_create_draft(self):
		response = self.client.post('/admin/content/page/add/', data={
			'title': 'test',
			'alias': 'test',
			'parent': '',
			'template': 'test.html',
			'content': '<p>This is a test</p>',
			'extra_header_content': '',
			'_newdraft': 'Save draft',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/?revision=1')

		created = Page.objects.get(pk=1)
		self.assertEqual(created.status, 'D')
		self.assertEqual(created.revisions.count(), 1)

		revision = created.revisions.first()
		self.assertEqual(revision.type, 'D')

	def _create_page(self, save=True):
		return Page(
			status='P',
			title='test',
			alias='test',
			template='test.html',
			content='<p>This is a test</p>',
			extra_header_content='',
			modified=now(),
			modifier=self.me,
		)

	def test_change_form_published(self):
		page = self._create_page()
		page.save()

		response = self.client.get('/admin/content/page/1/change/')
		self.assertEqual(response.context['original'], page)
		self.assertTrue('revision' not in response.context)
		self.assertContains(
			response,
			'<input type="submit" name="_newdraft" value="Save as a draft"/>',
			html=True, count=2
		)
		self.assertContains(
			response,
			'<input type="submit" name="_continue" value="Save and continue editing"/>',
			html=True, count=2
		)

		response = self.client.post('/admin/content/page/1/change/', data={
			'title': 'test 2',
			'alias': 'test',
			'parent': '',
			'template': 'test.html',
			'status': 'P',
			'content': '<p>This is a second test</p>',
			'extra_header_content': '',
			'_continue': 'Save and continue editing',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/')

		page = Page.objects.get(pk=1)
		self.assertEqual(page.status, 'P')
		self.assertEqual(page.title, 'test 2')
		self.assertEqual(page.content, '<p>This is a second test</p>')
		self.assertEqual(page.revisions.count(), 2)

		revision = page.revisions.last()
		self.assertEqual(revision.type, 'H')
		self.assertEqual(revision.title, 'test 2')
		self.assertEqual(revision.content, '<p>This is a second test</p>')

		response = self.client.post('/admin/content/page/1/change/', data={
			'title': 'test 3',
			'alias': 'test',
			'parent': '',
			'template': 'test.html',
			'status': 'P',
			'content': '<p>This is a third test</p>',
			'extra_header_content': '',
			'_newdraft': 'Save as a draft',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/?revision=3')

		page = Page.objects.get(pk=1)
		self.assertEqual(page.status, 'P')
		self.assertEqual(page.title, 'test 2')
		self.assertEqual(page.content, '<p>This is a second test</p>')
		self.assertEqual(page.revisions.count(), 3)

		revision = page.revisions.last()
		self.assertEqual(revision.type, 'D')
		self.assertEqual(revision.title, 'test 3')
		self.assertEqual(revision.content, '<p>This is a third test</p>')

	def test_change_form_draft(self):
		page = self._create_page(save=False)
		page.status = 'D'
		page.save()

		response = self.client.get('/admin/content/page/1/change/', follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/?revision=1')
		self.assertEqual(response.context['original'], page)
		self.assertEqual(response.context['revision'], page.revisions.first())
		self.assertContains(
			response,
			'<input type="submit" name="_continue" value="Save draft"/>',
			html=True, count=2
		)
		self.assertContains(
			response,
			'<input type="submit" name="_publish" value="Publish"/>',
			html=True, count=2
		)

		response = self.client.post('/admin/content/page/1/change/?revision=1', data={
			'title': 'test 2',
			'content': '<p>This is a second test</p>',
			'extra_header_content': '',
			'_continue': 'Save draft',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/?revision=1')

		page = Page.objects.get(pk=1)
		self.assertEqual(page.status, 'D')
		self.assertEqual(page.title, 'test 2')
		self.assertEqual(page.content, '<p>This is a second test</p>')
		self.assertEqual(page.revisions.count(), 1)

		revision = page.revisions.last()
		self.assertEqual(revision.type, 'D')
		self.assertEqual(revision.title, 'test 2')
		self.assertEqual(revision.content, '<p>This is a second test</p>')

		response = self.client.post('/admin/content/page/1/change/?revision=1', data={
			'title': 'test 3',
			'content': '<p>This is a third test</p>',
			'extra_header_content': '',
			'_publish': 'Publish',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/')

		page = Page.objects.get(pk=1)
		self.assertEqual(page.status, 'P')
		self.assertEqual(page.title, 'test 3')
		self.assertEqual(page.content, '<p>This is a third test</p>')
		self.assertEqual(page.revisions.count(), 1)

		revision = page.revisions.last()
		self.assertEqual(revision.type, 'H')
		self.assertEqual(revision.title, 'test 3')
		self.assertEqual(revision.content, '<p>This is a third test</p>')

	def test_change_form_history(self):
		page = self._create_page(save=False)
		page.save()
		revision = page.revisions.first()
		self.assertEqual(revision.type, 'H')

		response = self.client.get('/admin/content/page/1/change/', follow=True)
		self.assertEqual(response.status_code, 200)

		response = self.client.get('/admin/content/page/1/change/?revision=1')
		self.assertEqual(response.context['original'], page)
		self.assertEqual(response.context['revision'], revision)
		self.assertContains(
			response,
			'<input type="submit" name="_newdraft" value="Save as a draft"/>',
			html=True, count=2
		)
		self.assertContains(
			response,
			'<input type="submit" name="_publish" value="Save as current"/>',
			html=True, count=2
		)

		response = self.client.post('/admin/content/page/1/change/?revision=1', data={
			'title': 'test 2',
			'content': '<p>This is a second test</p>',
			'extra_header_content': '',
			'_newdraft': 'Save as a draft',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/?revision=2')

		page = Page.objects.get(pk=1)
		self.assertEqual(page.status, 'P')
		self.assertEqual(page.revisions.count(), 2)

		revision = page.revisions.last()
		self.assertEqual(revision.type, 'D')
		self.assertEqual(revision.title, 'test 2')
		self.assertEqual(revision.content, '<p>This is a second test</p>')

		response = self.client.post('/admin/content/page/1/change/?revision=1', data={
			'title': 'test 3',
			'content': '<p>This is a third test</p>',
			'extra_header_content': '',
			'_publish': 'Save as current',
		}, follow=True)
		self.assertRedirects(response, '/admin/content/page/1/change/')

		page = Page.objects.get(pk=1)
		self.assertEqual(page.status, 'P')
		self.assertEqual(page.title, 'test 3')
		self.assertEqual(page.content, '<p>This is a third test</p>')
		self.assertEqual(page.revisions.count(), 3)

		revision = page.revisions.last()
		self.assertEqual(revision.type, 'H')
		self.assertEqual(revision.title, 'test 3')
		self.assertEqual(revision.content, '<p>This is a third test</p>')
