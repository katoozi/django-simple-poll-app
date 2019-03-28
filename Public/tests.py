# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Item, Poll, Question, Vote
from .views import (LoginView, VoteResultJsonGenerator, VoteResultView,
                    VoteView, logout_view)


class PublicModelsTests(TestCase):
    def setUp(self):
        # set the redis connection
        self.redis_connection = settings.REDIS_CONNECTION
        # we use factory for simulate the http requests
        self.factory = RequestFactory()
        # a user object for create database records
        self.user = User.objects.create_user(
            username="testing_lover", password="i_love_testing"
        )
        self.poll = Poll.objects.create(title="Testing", is_published=False)
        self.question = Question.objects.create(title="Testing is ?", column=1)
        self.items = [
            Item.objects.create(question=self.question, value="Good", pos=0),
            Item.objects.create(question=self.question, value="Bad", pos=1),
            Item.objects.create(question=self.question, value="Awful", pos=2),
        ]
        self.poll.questions.add(self.question)
        self.vote = Vote.objects.create(
            user=self.user,
            question=self.question,
            poll=self.poll,
            ip="127.0.0.1",
            item=self.items[0]
        )

    def tearDown(self):
        # remove all redis keys after tests are done, because django does not simulate redis db
        self.redis_connection.flushall()

    def test_poll_model(self):
        # Poll model asserts
        polls = Poll.published.all()
        self.assertFalse(
            polls.exists(), "Poll Published Manager Does Not Work!")

        self.assertEqual(str(self.poll), "Testing",
                         "__str__ Of Poll Model Have Issue!")
        self.assertEqual(self.poll.__unicode__(), "Testing",
                         "__unicode__ Of Poll Model Have Issue!")
        poll_questions = self.poll.questions.all()
        self.assertTrue(poll_questions.exists(),
                        "Poll ManyToMany Relation Does Not Work!")

        user_polls = Poll.published.exclude_user_old_votes(self.user.pk).all()
        self.assertFalse(user_polls.exists(),
                         "exclude_user_old_votes In Published Manager of Poll Model have Issue!,"
                         "Because Poll Not Published")

        self.assertEqual(self.poll.get_vote_count(), None,
                         "Poll poll_vote_count attribute Does Not Wotk Currectly!")
        self.redis_connection.incr("poll:%s" % (self.poll.pk))
        self.assertEqual(int(self.poll.get_vote_count()), 1,
                         "Poll poll_vote_count attribute Does Not Wotk Currectly!")

    def test_question_model(self):
        # Question Model Asserts
        self.assertEqual(str(self.question), "Testing is ?",
                         "__str__ Of Question Model Have Issue!")
        self.assertEqual(self.question.__unicode__(), "Testing is ?",
                         "__unicode__ Of Question Model Have Issue!")

    def test_item_model(self):
        # Item Model Asserts
        item = self.items[0]
        self.assertEqual(str(item), "Good",
                         "__str__ Of Item Model Have Issue!")
        self.assertEqual(item.__unicode__(), "Good",
                         "__unicode__ Of Item Model Have Issue!")
        self.assertEqual(item.question.title, "Testing is ?",
                         "Item Model ForeignKey Does Not Work!")
        self.assertEqual(item.question.poll_qustions.first().title, "Testing",
                         "item -> question -> poll_questions -> First() -> title Does Not Work!")
        self.assertEqual(int(item.get_vote_count(
            self.poll.id, self.question.id)), 1, "vote count does not save currectly in redis")

    def test_vote_model(self):
        # Vote Model Asserts
        self.assertEqual(str(self.vote), self.user.username,
                         "__str__ Of Vote Model Have Issue!")
        self.assertEqual(str(self.vote.__unicode__()),
                         self.user.username, "__unicode__ Of Vote Model Have Issue!")


class PublicViewsTests(TestCase):
    def setUp(self):
        self.super_user = User.objects.create_user(
            username="testing_lover_super_user", password="i_love_testing", is_superuser=True, is_staff=True
        )
        self.anonymous_user = User.objects.create_user(
            username="testing_lover_anonymous_user", password="i_love_testing"
        )

    def test_LoginViewGetRequest(self):
        # Test Get Requets Without User Login
        response = self.client.get(reverse("public:login"))
        self.assertEqual(response.status_code, 200,
                         "Login View Send %s Instead of 200" % response.status_code)

        # Test Get Request With Anonymous User Login
        self.client.login(
            username="testing_lover_anonymous_user", password="i_love_testing")
        response = self.client.get(reverse("public:login"), follow=True)
        self.assertRedirects(response, reverse("public:vote"))

        # Test Get Request With Super User Login
        self.client.login(
            username="testing_lover_super_user", password="i_love_testing")
        response = self.client.get(reverse("public:login"), follow=True)
        self.assertRedirects(response, reverse(
            "public:view_result", kwargs={'chart_type': "pie"}))

    def test_LoginViewPostRequest(self):
        # Logout all login users
        self.client.logout()
