# -*- coding: utf-8 -*-
from django import forms
from django.conf.urls.defaults import url as django_url
from django.core.exceptions import ImproperlyConfigured
from django.forms.formsets import BaseFormSet
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404

from ajax_validation.utils import LazyEncoder


class ModelValidationView(object):
    model = None
    form_class = None
    save_if_valid = False
    url_pattern = None
    url_name = None

    def __init__(self, model=None, form_class=None, save_if_valid=False, url_pattern=None, url_name=None):
        self.model = model or self.__class__.model
        self.form_class = form_class or self.__class__.form_class
        self.save_if_valid = save_if_valid or self.__class__.save_if_valid
        self.url_pattern = url_pattern or self.__class__.url_pattern
        self.url_name = url_name or self.__class__.url_name

    def get_model(self):
        if not self.model:
            raise ImproperlyConfigured('`model` have to be setup on ModelValidationView instance')
        return self.model

    def get_form_class(self):
        if not self.form_class:
            model = self.get_model()
            self.form_class = modelform_factory(model)
        return self.form_class

    def _get_app_and_model_names(self):
        model = self.get_model()
        return {
            'app_name': model._meta.app_label.lower(),
            'model_name': model._meta.object_name.lower(),
            }

    def get_url_pattern(self, url_prefix=''):
        if self.url_pattern:
            return self.url_pattern
        ctx = self._get_app_and_model_names()
        ctx.update(url_prefix=url_prefix)
        return r'^%(url_prefix)s%(app_name)s/%(model_name)s/(?P<object_pk>\d+)?$' % ctx

    def get_url_name(self):
        if self.url_name:
            return self.url_name
        ctx = self._get_app_and_model_names()
        return 'validate-%(app_name)s-%(model_name)s' % ctx

    def get_url(self, url_prefix=''):
        return django_url(
            self.get_url_pattern(url_prefix=url_prefix),
            self.validate,
            name=self.get_url_name())
    url = property(lambda s: s.get_url())

    def get_instance(self, request, *args, **kwargs):
        object_pk = kwargs.get('object_pk', None)
        model = self.get_model()
        if object_pk:
            return get_object_or_404(model, pk=object_pk)
        return model()

    def get_form_kwargs(self, request, *args, **kwargs):
        instance = self.get_instance(request, *args, **kwargs)
        return dict(data=request.POST, instance=instance)

    def save(self, request, form):
        form.save()
        return {}

    def get_form_error_and_formfields(self, form):
        """
        Returns form errors and formfields. Taking formsets into account.
        """
        # if we're dealing with a FormSet then walk over .forms to populate errors and formfields
        if isinstance(form, BaseFormSet):
            errors = {}
            formfields = {}
            for f in form.forms:
                for field in f.fields.keys():
                    formfields[f.add_prefix(field)] = f[field]
                for field, error in f.errors.iteritems():
                    errors[f.add_prefix(field)] = error

            if form.non_form_errors():
                errors['__all__'] = form.non_form_errors()

        else:
            errors = form.errors
            formfields = dict([(fieldname, form[fieldname]) for fieldname in form.fields.keys()])

        return errors, formfields

    def get_formfield_id(self, key, formfields):
        if '__all__' == key:
            return key
        formfield = formfields[key]
        if not isinstance(formfield.field, forms.FileField):
            html_id = formfield.field.widget.attrs.get('id') or formfield.auto_id
            html_id = formfield.field.widget.id_for_label(html_id)
            return html_id
        return None

    def validate(self, request, *args, **kwargs):
        if request.method != 'POST':
            return HttpResponseNotAllowed('Sorry, validation views required to use POST method')

        form_class = kwargs.pop('form_class', self.get_form_class())
        if not form_class:
            raise ImproperlyConfigured('form_class param have to be provided.')

        save_if_valid = kwargs.pop('save_if_valid', self.save_if_valid)
        save_fun = self.save if save_if_valid else lambda r, f: {}

        form = form_class(**self.get_form_kwargs(request, *args, **kwargs))
        data = {}

        if form.is_valid():
            data.update(valid=True, **save_fun(request, form))
        else:
            errors, formfields = self.get_form_error_and_formfields(form)
            # if fields have been specified then restrict the error list
            if request.POST.getlist('fields[]'):
                fields = request.POST.getlist('fields[]') + ['__all__']
                errors = dict((key, val) for key, val in errors.iteritems() if key in fields)

            final_errors = {}
            for key, val in errors.iteritems():
                key_id = self.get_formfield_id(key, formfields)
                if key_id:
                    final_errors[key_id] = val

            data.update(valid=not final_errors, errors=final_errors)

        json_serializer = LazyEncoder()
        return HttpResponse(json_serializer.encode(data), mimetype='application/json')
