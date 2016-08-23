from __future__ import absolute_import, unicode_literals

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Contact, ContactField


@receiver(post_save, sender=Contact)
def set_data_field_values(sender, instance, **kwargs):
    """Hook to update the field values for a Contact.

    Stores all values, even for DataFields that are not visible.
    By doing this, we can quickly show meaningful data when DataField
    visibility is toggled.
    """
    if not hasattr(instance, '_data_field_values'):
        return

    if instance._data_field_values is not None:
        data_fields = {f.key: f for f in instance.org.datafield_set.all()}
        for key, value in instance._data_field_values.items():
            if key not in data_fields:
                continue  # Don't update fields we don't have a record for.

            # Remove empty strings for consistency with RapidPro.
            value = value or None

            contact_field, _ = ContactField.objects.get_or_create(
                contact=instance, field=data_fields[key])
            contact_field.set_value(value)
            contact_field.save()

    del instance._data_field_values
