# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns

from ajax_validation.views import ModelValidationView


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class ValidationSite(object):
    def __init__(self):
        self._registry = {}

    def _get_iterable(self, validation_class_or_iterable):
        if not isinstance(validation_class_or_iterable, ModelValidationView):
            validation_class_or_iterable = [validation_class_or_iterable]
        return validation_class_or_iterable

    def register(self, validation_class_or_iterable):
        validation_class_iterable = self._get_iterable(validation_class_or_iterable)

        for validation_class in validation_class_iterable:
            if validation_class in self._registry:
                raise AlreadyRegistered('The validation_class %s is already registered' % validation_class.__name__)

            self._registry[validation_class] = validation_class()

    def unregister(self, validation_class_or_iterable):
        validation_class_iterable = self._get_iterable(validation_class_or_iterable)

        for validation_class in validation_class_iterable:
            if validation_class not in self._registry:
                raise NotRegistered('The validation_class %s is not registered' % validation_class.__name__)
            del self._registry[validation_class]

    def get_urls(self, url_prefix=''):
        urlpatterns = patterns('')
        for model, modelvalidationview in self._registry.iteritems():
            urlpatterns += patterns('', modelvalidationview.get_url(url_prefix=url_prefix))
        return urlpatterns
    urls = property(lambda s: s.get_urls())


site = ValidationSite()
