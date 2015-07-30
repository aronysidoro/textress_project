from django import forms
from django.conf import settings
from django.test import TestCase, LiveServerTestCase, RequestFactory
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from model_mommy import mommy

from main.tests.factory import create_hotel
from utils import create, login_messages


class AuthTests(TestCase):

    def setUp(self):
        # Groups
        create._get_groups_and_perms()
        # User
        self.password = '1234'
        self.user = User.objects.create_user('Bobby',
            settings.DEFAULT_FROM_EMAIL, self.password)
        # add Hotel
        self.hotel = create_hotel()
        self.user.profile.update_hotel(self.hotel)

    def test_login(self):
        response = self.client.get(reverse('logout'))
        with self.assertRaises(TypeError):
            assert response.context['user'].username != self.user.username

        response = self.client.post(reverse('login'),
                        {'username': self.user,
                        'password': self.password}, follow=True)
        self.assertRedirects(response, reverse('account'))
        assert response.context['user'].username == self.user.username
        # login success message rendered
        m = list(response.context['messages'])
        self.assertEqual(len(m), 1)
        self.assertEqual(str(m[0]), login_messages['now_logged_in'])

    def test_logout(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(reverse('logout'))
        assert response.status_code == 302
        with self.assertRaises(TypeError):
            assert not response.context['user']


class PasswordChangeFormTests(TestCase):

    def setUp(self):
        self.password = '1111'
        self.new_password = '2222'
        self.user = User.objects.create_user('Bobby',
            settings.DEFAULT_FROM_EMAIL, self.password)

    def test_post(self):
        # login w/ orig password
        self.client.login(username=self.user.username, password=self.password)

        # change password
        response = self.client.post(reverse('password_change'),
            {'old_password': self.password,
            'new_password1': self.new_password,
            'new_password2': self.new_password
            }, follow=True)
        self.assertRedirects(response, reverse('password_change_done'))
        response = self.client.get(reverse('logout'))
        
        # login w/ new password
        response = self.client.post(reverse('login'),
                        {'username': self.user,
                        'password': self.new_password}, follow=True)
        self.assertRedirects(response, reverse('account'))
        assert response.context['user'].username == self.user.username