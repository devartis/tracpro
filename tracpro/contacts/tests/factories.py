from __future__ import unicode_literals

import random

import factory
import factory.fuzzy

from tracpro.test import factory_utils

from .. import models


__all__ = ['Contact', 'TwitterContact', 'PhoneContact', 'DataField', 'ContactField']


class Contact(factory_utils.SmartModelFactory):
    uuid = factory_utils.FuzzyUUID()
    org = factory.SubFactory("tracpro.test.factories.Org")
    urn = factory.Sequence(lambda n: random.choice(("twitter:contact", "tel:123")) + str(n))
    language = 'eng'

    class Meta:
        model = 'contacts.Contact'

    @factory.lazy_attribute
    def region(self):
        from tracpro.test.factories import Region
        return Region(org=self.org)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for group in extracted:
                self.groups.add(group)


class TwitterContact(Contact):
    urn = factory.Sequence(lambda n: "twitter:contact" + str(n))


class PhoneContact(Contact):
    urn = factory.Sequence(lambda n: "tel:123" + str(n))


class DataField(factory.django.DjangoModelFactory):
    org = factory.SubFactory("tracpro.test.factories.Org")
    key = factory.fuzzy.FuzzyText()
    value_type = models.DataField.TYPE_TEXT

    class Meta:
        model = 'contacts.DataField'


class ContactField(factory.django.DjangoModelFactory):
    contact = factory.SubFactory("tracpro.test.factories.Contact")
    field = factory.SubFactory("tracpro.test.factories.DataField")

    class Meta:
        model = 'contacts.ContactField'
