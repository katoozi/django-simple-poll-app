# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Item, Poll, Question, Vote


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
        # remove all redis keys after tests are done
        # because django does not simulate redis db
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
        self.assertFalse(
            user_polls.exists(),
            "exclude_user_old_votes In Published "
            "Manager of Poll Model have Issue!,Because Poll Not Published")

        self.assertEqual(
            self.poll.get_vote_count(),
            None, "Poll poll_vote_count attribute Does Not Wotk Currectly!")
        self.redis_connection.incr("poll:%s" % (self.poll.pk))
        self.assertEqual(
            int(self.poll.get_vote_count()),
            1, "Poll poll_vote_count attribute Does Not Wotk Currectly!")

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
        self.assertEqual(
            item.question.poll_qustions.first().title, "Testing",
            "item -> question -> poll_questions -> First() -> "
            "title Does Not Work!")
        self.assertEqual(
            int(item.get_vote_count(self.poll.id, self.question.id)),
            1, "vote count does not save currectly in redis")

    def test_vote_model(self):
        # Vote Model Asserts
        self.assertEqual(str(self.vote), self.user.username,
                         "__str__ Of Vote Model Have Issue!")
        self.assertEqual(str(self.vote.__unicode__()),
                         self.user.username,
                         "__unicode__ Of Vote Model Have Issue!")


class PublicViewsTests(TestCase):
    def setUp(self):
        self.redis_connection = settings.REDIS_CONNECTION
        self.factory = RequestFactory()
        self.super_user = User.objects.create_user(
            username="testing_lover_super_user", password="i_love_testing",
            is_superuser=True, is_staff=True)
        self.anonymous_user = User.objects.create_user(
            username="testing_lover_anonymous_user", password="i_love_testing"
        )

    def tearDown(self):
        # remove all redis keys after tests are done
        # because django does not simulate redis db
        self.redis_connection.flushall()

    def test_LoginViewGetRequest(self):
        # Test Get Requets Without User Login
        response = self.client.get(reverse("public:login"))
        self.assertEqual(
            response.status_code, 200, "Login View Send %s Instead of 200" %
            response.status_code)

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
        # Remove all session
        self.client.logout()

        # Test LoginForm not Valid Situation
        response = self.client.post(reverse("public:login"), {
            "username": "testing_lover_anonymous_user",
            "remember_me": "True"
        })
        self.assertFormError(response, 'form', "password",
                             "This field is required.")

        # Test user With This credentials Does Not Exist.
        response = self.client.post(reverse("public:login"), {
            "username": "testing_lover_anonymous_user",
            "password": "TruekslMDsMDFLkmsdLkfmksdkf"  # wrong password
        })
        self.assertEqual(
            response.context['message'],
            'User With This credentials Does Not Exists.',
            "auhtenticate Does Not Work!")

        # Test Anonymous User After Login Redirect To
        response = self.client.post(reverse("public:login"), {
            "username": "testing_lover_anonymous_user",
            "password": "i_love_testing",  # wrong password
            "remember_me": "True"
        })
        self.assertRedirects(response, reverse("public:vote"))

        # Test Super User After Login Redirect To
        response = self.client.post(reverse("public:login"), {
            "username": "testing_lover_super_user",
            "password": "i_love_testing"  # wrong password
        })
        self.assertRedirects(response, reverse(
            "public:view_result", kwargs={'chart_type': "pie"}))

        # Test Super User After Login Redirect To With next in url
        response = self.client.post(reverse("public:login") + "?next=/admin/",
                                    {
            "username": "testing_lover_super_user",
            "password": "i_love_testing",  # wrong password
        })
        self.assertRedirects(response, reverse("admin:index"))

    def test_VoteViewGetRequest(self):
        # Test the poll context object
        self.client.login(username=self.anonymous_user.username,
                          password="i_love_testing")
        response = self.client.get(reverse("public:vote"))
        self.assertFalse(response.context['polls'].exists(
        ), "polls object must be False because poll not published!")

        # Test the super ans staff users redirection
        self.client.login(username=self.super_user.username,
                          password="i_love_testing")
        response = self.client.post(reverse("public:vote"))
        self.assertRedirects(response, reverse(
            "public:view_result", kwargs={'chart_type': "pie"}))

        # Test the request post data does not have poll_id key
        self.client.login(username=self.anonymous_user.username,
                          password="i_love_testing")
        response = self.client.post(reverse("public:vote"), {"1:3": "1"})
        self.assertEqual(
            response.context['message'],
            "poll_id Does Not Exist!", "check poll_id key does not work!")

        # Test poll with this id does not exist.
        self.client.login(username=self.anonymous_user.username,
                          password="i_love_testing")
        response = self.client.post(
            reverse("public:vote"), {"poll_id": "5155156"})
        self.assertEqual(
            response.context['message'],
            "poll with this id does not exist.",
            "fetch poll with this id does not Work!")

    def test_VoteResultView(self):
        # Test anonymous users redirection
        self.client.login(username=self.anonymous_user.username,
                          password="i_love_testing")
        response = self.client.get(
            reverse("public:view_result", kwargs={'chart_type': "pie"}))
        self.assertRedirects(response, reverse("public:vote"))

        # Test unknown chart type
        self.client.login(username=self.super_user.username,
                          password="i_love_testing")
        response = self.client.get(
            reverse(
                "public:view_result",
                kwargs={'chart_type': "kdfsdfmksdm"}))
        self.assertEqual(
            response.context['chart_type'],
            "pie", "Default chart type must be pie!")

    def test_VoteResultJsonGenerator(self):
        # Test anonymous users redirection
        self.client.login(username=self.anonymous_user.username,
                          password="i_love_testing")
        response = self.client.get(
            reverse(
                "public:view_result_json_generator",
                kwargs={'poll_id': "1", "question_id": 1}))
        self.assertRedirects(response, reverse("public:vote"))

        # Test Poll With This Id Does not Exist. JsonResponse
        self.client.login(username=self.super_user.username,
                          password="i_love_testing")
        response = self.client.get(
            reverse(
                "public:view_result_json_generator",
                kwargs={'poll_id': "1", "question_id": 1}))
        self.assertJSONEqual(str(response.content, encoding="utf-8"),
                             {"Error": "Poll With That Id Does not Exist."})

        # Test Poll Does Not Have Question With This Id
        self.client.login(username=self.super_user.username,
                          password="i_love_testing")
        poll = Poll.objects.create(title="Testing", is_published=True)
        response = self.client.get(
            reverse(
                "public:view_result_json_generator",
                kwargs={'poll_id': poll.id, "question_id": 1}))
        self.assertJSONEqual(
            str(response.content, encoding="utf-8"),
            {"Error": "Question With That Id Does not belong to This Poll"})

        # Test other remain block code
        question = Question.objects.create(title="Testing Is ?", column=4)
        poll.questions.add(question)
        Item.objects.create(value="Good", pos=0, question=question)
        Item.objects.create(value="Bad", pos=0, question=question)
        Item.objects.create(value="Awful", pos=0, question=question)
        self.client.login(username=self.super_user.username,
                          password="i_love_testing")
        response = self.client.get(
            reverse(
                "public:view_result_json_generator",
                kwargs={'poll_id': poll.id, "question_id": question.id}))
