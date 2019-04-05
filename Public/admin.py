from django.contrib import admin
from django.utils.translation import gettext as _
from easy_select2 import select2_modelform

from .models import Item, Poll, Question, Vote


class PollAdminPanel(admin.ModelAdmin):
    model = Poll
    filter_horizontal = ('questions',)
    list_display = ['title', 'is_published', 'poll_vote_count']
    list_filter = ['is_published']
    search_fields = ['title']


class ItemForQuestionInline(admin.TabularInline):
    model = Item
    extra = 0
    can_delete = True


class QuestionAdminPanel(admin.ModelAdmin):
    model = Question
    list_display = ['title', 'column']
    inlines = [ItemForQuestionInline, ]
    search_fields = ['title', 'column']


class ItemAdminPanel(admin.ModelAdmin):
    form = select2_modelform(Item, attrs={'width': '300px'})
    model = Item
    list_display = ['question', 'value', 'pos']
    search_fields = ['value', 'pos', 'question__title']


class VoteAdminPanel(admin.ModelAdmin):
    # disable add permission because we don't wan to cheat on votes
    def has_add_permission(self, request):
        return False

    # disable delete permission because we don't wan to cheat on votes
    def has_delete_permission(self, request, obj=None):
        return False

    # remove delete action from vote model actions
    # because we don't have delete permission anymore
    def get_actions(self, request):
        return []

    form = select2_modelform(Vote, attrs={'width': '300px'})
    model = Vote
    list_display = ['poll', 'user', 'ip', 'vote_time']
    search_fields = ['ip', 'vote_time', 'user__username',
                     'user__email', 'poll__title', 'question__title']
    readonly_fields = ['user', 'poll', 'question', 'item', 'vote_time', 'ip']


admin.site.site_title = _("Poll System")
admin.site.site_header = _("Poll System")

admin.site.register(Poll, PollAdminPanel)
admin.site.register(Question, QuestionAdminPanel)
admin.site.register(Item, ItemAdminPanel)
admin.site.register(Vote, VoteAdminPanel)
