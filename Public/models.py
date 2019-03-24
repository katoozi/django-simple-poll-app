# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.manager import Manager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

User = get_user_model()
redis_con = settings.REDIS_CONNECTION


class Question(models.Model):
    title = models.CharField(max_length=250, verbose_name=_('Question'))

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    def get_vote_count(self):
        return Vote.objects.filter(question=self).count()
    question_vote_count = property(fget=get_vote_count)

    class Meta:
        ordering = ['-id']
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')


class Item(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="question_answers")
    value = models.CharField(max_length=250, verbose_name=_('value'))
    pos = models.SmallIntegerField(default='0', verbose_name=_('position'))

    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        ordering = ['pos']

    def __str__(self):
        return self.value

    def __unicode__(self):
        return self.value

    def get_vote_count(self):
        return Vote.objects.filter(item=self).count()
    item_vote_count = property(fget=get_vote_count)


class PublishedManager(Manager):
    def get_queryset(self):
        return super(PublishedManager, self).get_queryset().filter(is_published=True)

    def exclude_user_old_votes(self, user_id):
        # get poll ids that user already votes, we save them in redis for reduce sql querys
        # remember that you have to enable Redis Persistence
        user_votes = list(redis_con.smembers(str(user_id)))

        return self.get_queryset().exclude(pk__in=user_votes)


class Poll(models.Model):
    title = models.CharField(max_length=250, verbose_name=_('Poll Title'))
    questions = models.ManyToManyField(Question, related_name="poll_qustions")
    is_published = models.BooleanField(
        default=True, verbose_name=_('is published'))

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = _('poll')
        verbose_name_plural = _('polls')

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    def get_vote_count(self):
        return Vote.objects.filter(poll=self).count()
    poll_vote_count = property(fget=get_vote_count)


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll, on_delete=models.CASCADE, verbose_name=_('poll'))
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, verbose_name=_('question'))
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, verbose_name=_('voted item'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                             verbose_name=_('user'))
    ip = models.GenericIPAddressField(verbose_name=_('user\'s IP'))
    vote_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    def __unicode__(self):
        return self.user.username


@receiver(post_save, sender=Vote)
def vote_post_save_receiver(sender, instance, **kwargs):
    redis_con.sadd(str(instance.user.pk), instance.pk)
