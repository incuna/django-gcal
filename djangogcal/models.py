"""
djangogcal.models


"""

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

class CalendarEventManager(models.Manager):
    """
    A custom manager for CalendarEvent models, containing utility methods for
    dealing with content-types framework.
    """
    
    def get_event_id(self, obj, feed_id):
        """
        Gets the Google Calendar event-id for a model, or returns None.
        """
        ct = ContentType.objects.get_for_model(obj)
        try:
            event = self.get(content_type=ct, object_id=obj.pk, feed_id=feed_id)
            event_id = event.event_id
        except models.ObjectDoesNotExist:
            event_id = None
        return event_id
    
    def set_event_id(self, obj, feed_id, event_id):
        """
        Sets the Google Calendar event-id for a model.
        """
        ct = ContentType.objects.get_for_model(obj)
        try:
            event = self.get(content_type=ct, object_id=obj.pk, feed_id=feed_id)
            event.event_id = event_id
        except models.ObjectDoesNotExist:
            event = CalendarEvent(content_type=ct, object_id=obj.pk,
                                  feed_id=feed_id, event_id=event_id)
        event.save()
    
    def delete_event_id(self, obj, feed_id):
        """
        Deletes the record containing the event-id for a model.
        """
        ct = ContentType.objects.get_for_model(obj)
        try:
            event = self.get(content_type=ct, object_id=obj.pk, feed_id=feed_id)
            event.delete()
        except models.ObjectDoesNotExist:
            pass

class CalendarEvent(models.Model):
    """
    
    """
    
    # django.contrib.contenttypes 'magic'
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey()
    
    # google calendar event_id and feed_id
    event_id = models.CharField(max_length=255)
    feed_id = models.CharField(max_length=255)
    
    # custom manager
    objects = CalendarEventManager()
    
    def __unicode__(self):
        """ Returns the string representation of the CalendarEvent. """
        return u"%s: (%s, %s)" % (self.object, self.feed_id, self.event_id)
