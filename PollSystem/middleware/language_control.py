# -*- coding: utf-8 -*-
from django.shortcuts import redirect
from django.utils import translation


class LanguageControl(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        url_list = request.get_full_path().split('/')
        if url_list[1] == 'en' or url_list[1] == 'fa':
            language = translation.get_language_from_request(request)
            if url_list[1] == 'en' and language == 'en':
                return self.get_response(request)
            elif url_list[1] == 'fa' and language == 'fa':
                return self.get_response(request)
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()
            return redirect(request.get_full_path()[3:])
        return self.get_response(request)


class LanguageObject(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']
        return self.get_response(request)
