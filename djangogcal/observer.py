"""
djangogcal.observer


"""

from django.db.models import signals
from gdata.calendar import SendEventNotifications
from gdata.calendar.data import CalendarEventEntry
from gdata.calendar.client import CalendarClient

from models import CalendarEvent

class CalendarObserver(object):
    """
    
    """
    
    DEFAULT_FEED = '/calendar/feeds/default/private/full'
    
    def __init__(self, email, password, feed=DEFAULT_FEED, client=None):
        """
        Initialize an instance of the CalendarObserver class.
        """
        self.adapters = {}
        self.email = email
        self.password = password
        self.feed = feed
        self.client = client
    
    def observe(self, model, adapter):
        """
        Establishes a connection between the model and Google Calendar, using
        adapter to transform data.
        """
        self.adapters[model] = adapter
        signals.post_save.connect(self.on_update, sender=model,
                                  dispatch_uid="djangogcal post-save signal")
        signals.post_delete.connect(self.on_delete, sender=model,
                                    dispatch_uid="djangogcal post-delete signal")
    
    def observe_related(self, model, related, selector):
        """
        Updates the Google Calendar entry for model when the related model is
        changed or deleted.  Selector should be a function object which accepts
        an instance of related as a parameter and returns an instance of type
        model.
        """
        def on_related_update(**kwargs):
            self.update(model, selector(kwargs['instance']))
        signals.post_save.connect(on_related_update, sender=related, weak=False)
        signals.post_delete.connect(on_related_update, sender=related,
                                    weak=False)
    
    def on_update(self, **kwargs):
        """
        Called by Django's signal mechanism when an observed model is updated.
        """
        self.update(kwargs['sender'], kwargs['instance'])
    
    def on_delete(self, **kwargs):
        """
        Called by Django's signal mechanism when an observed model is deleted.
        """
        self.delete(kwargs['sender'], kwargs['instance'])
    
    def get_client(self):
        """
        Get an authenticated gdata.calendar.client.CalendarClient instance.
        """
        if self.client is None:
            self.client = CalendarClient(source='django-gcal')
            self.client.ClientLogin(self.email, self.password, self.client.source)
        return self.client
    
    def get_event(self, client, instance, feed=None):
        """
        Retrieves the specified event from Google Calendar, or returns None
        if the retrieval fails.
        """
        if feed is None:
            feed = self.feed
        event_id = CalendarEvent.objects.get_event_id(instance, feed)
        try:
            event = client.GetCalendarEntry(event_id)
        except Exception:
            event = None
        return event
    
    def update(self, sender, instance):
        """
        Update or create an entry in Google Calendar for the given instance
        of the sender model type.
        """
        adapter = self.adapters[sender]
        if adapter.can_save(instance):
            client = self.get_client()
            feed = adapter.get_feed_url(instance) or self.feed
            event = self.get_event(client, instance, feed) or CalendarEventEntry()
            adapter.get_event_data(instance).populate_event(event)
            if adapter.can_notify(instance):
                event.send_event_notifications = SendEventNotifications(
                    value='true')
            if event.GetEditLink():
                client.Update(event)
            else:
                new_event = client.InsertEvent(event, insert_uri=feed)
                CalendarEvent.objects.set_event_id(instance, feed,
                                                   new_event.get_edit_link().href)
    
    def delete(self, sender, instance):
        """
        Delete the entry in Google Calendar corresponding to the given instance
        of the sender model type.
        """
        adapter = self.adapters[sender]
        feed = adapter.get_feed_url(instance) or self.feed
        if adapter.can_delete(instance):
            client = self.get_client()
            event = self.get_event(client, instance, feed)
            if event:
                if adapter.can_notify(instance):
                    event.send_event_notifications = SendEventNotifications(
                        value='true')
                client.Delete(event)
        CalendarEvent.objects.delete_event_id(instance, feed)
