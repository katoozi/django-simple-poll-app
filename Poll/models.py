# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.manager import Manager
from django.utils.translation import gettext as _

User = get_user_model()


class PublishedManager(Manager):
    def get_query_set(self):
        return super(PublishedManager, self).get_query_set().filter(is_published=True)


class Question(models.Model):
    title = models.CharField(max_length=250, verbose_name=_('Question'))
    date = models.DateField(verbose_name=_(
        'date'), default=datetime.date.today)
    is_published = models.BooleanField(
        default=True, verbose_name=_('is published'))

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ['-id']
        verbose_name = _('poll')
        verbose_name_plural = _('polls')


class Poll(models.Model):
    title = models.CharField(max_length=250, verbose_name=_('Poll Title'))
    questions = models.ManyToManyField(Question, related_name="qustions")

    class Meta:
        verbose_name = _('poll')
        verbose_name_plural = _('polls')

    def __str__(self):
        return self.title
    
    def __unicode__(self):
        return self.title

    def get_vote_count(self):
        return Vote.objects.filter(poll=self).count()
    vote_count = property(fget=get_vote_count)

    def get_cookie_name(self):
        return 'poll_%s' % self.pk


class Item(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.CharField(max_length=250, verbose_name=_('value'))
    pos = models.SmallIntegerField(default='0', verbose_name=_('position'))

    class Meta:
        verbose_name = _('answer')
        verbose_name_plural = _('answers')
        ordering = ['pos']

    def __str__(self):
        return u'%s' % (self.value,)
    
    def __unicode__(self):
        return u'%s' % (self.value,)

    def get_vote_count(self):
        return Vote.objects.filter(item=self).count()
    vote_count = property(fget=get_vote_count)


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll, on_delete=models.CASCADE, verbose_name=_('poll'))
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, verbose_name=_('voted item'))
    ip = models.GenericIPAddressField(verbose_name=_('user\'s IP'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                             verbose_name=_('user'))
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('vote')
        verbose_name_plural = _('votes')
    
    def __unicode__(self):
        if isinstance(User, str):
            UserModel = get_user_model()
        else:
            UserModel = User

        if isinstance(self.user, UserModel):
            username_field = getattr(User, 'USERNAME_FIELD', 'username')
            return getattr(User, username_field, '')
        return self.ip 

    def __str__(self):
        if isinstance(User, str):
            UserModel = get_user_model()
        else:
            UserModel = User

        if isinstance(self.user, UserModel):
            username_field = getattr(User, 'USERNAME_FIELD', 'username')
            return getattr(User, username_field, '')
        return self.ip
