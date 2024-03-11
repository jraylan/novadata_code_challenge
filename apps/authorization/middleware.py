# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, Resolver404, reverse, resolve
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class AuthorizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        try:
            self.LOGIN_URL = reverse(settings.LOGIN_URL_NAME)
        except:
            raise ImproperlyConfigured('A configuração necessária LOGIN_URL_NAME não foi definido')
        
        self.PUBLIC_URL_NANES = [
            settings.LOGIN_URL_NAME,
            *getattr(settings, 'PUBLIC_URL_NAMES', [])
        ]
        
        

    def __call__(self, request):
        resolved_url = resolve(request.path)

        url_name = resolved_url.url_name
        is_public = url_name in self.PUBLIC_URL_NANES

        if not is_public and not request.user.is_authenticated:
            return HttpResponseRedirect(self.LOGIN_URL)

        response = self.get_response(request)
        return response
