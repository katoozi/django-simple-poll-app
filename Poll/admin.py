from django.contrib import admin
from django.utils.translation import gettext as _

from .models import Poll, Vote, Item


class PollItemInline(admin.TabularInline):
    model = Item
    extra = 0
    max_num = 15


class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'vote_count', 'is_published')
    inlines = [PollItemInline, ]


class VoteAdmin(admin.ModelAdmin):
    list_display = ('poll', 'ip', 'user', 'datetime')
    list_filter = ('poll', 'datetime')


admin.site.register(Vote, VoteAdmin)
admin.site.register(Poll, PollAdmin)
