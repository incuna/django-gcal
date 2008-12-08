"""
djangogcal.observer


"""

from django.db.models import signals
from gdata.calendar import CalendarEventEntry, SendEventNotifications
from gdata.calendar.service import CalendarService

from models import CalendarEvent

class CalendarObserver(object):
    """
    
    """
    
    DEFAULT_FEED = '/calendar/feeds/default/private/full'
    
    def __init__(self, email, password, feed=DEFAULT_FEED, service=None):
        """
        Initialize an instance of the CalendarObserver class.
        """
        self.adapters = {}
        self.email = email
        self.password = password
        self.feed = feed
        self.service = service
    
    def observe(self, model, adapter):
        """
        Establishes a connection between the model and Google Calendar, using
        adapter to transform data.
        """
        self.adapters[model] = adapter
        signals.post_save.connect(self.on_update, sender=model)
        signals.post_delete.connect(self.on_delete, sender=model)
    
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
    
    def get_service(self):
        """
        Get an authenticated gdata.calendar.service.CalendarService instance.
        """
        if self.service is None:
            self.service = CalendarService(email=self.email,
                                           password=self.password)
            self.service.ProgrammaticLogin()
        return self.service
    
    def get_event(self, service, instance):
        """
        Retrieves the specified event from Google Calendar, or returns None
        if the retrieval fails.
        """
        event_id = CalendarEvent.objects.get_event_id(instance, self.feed)
        try:
            event = service.GetCalendarEventEntry(event_id)
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
            service = self.get_service()
            event = self.get_event(service, instance) or CalendarEventEntry()
            adapter.get_event_data(instance).populate_event(event)
            if adapter.can_notify(instance):
                event.send_event_notifications = SendEventNotifications(
                    value='true')
            if event.GetEditLink():
                service.UpdateEvent(event.GetEditLink().href, event)
            else:
                new_event = service.InsertEvent(event, self.feed)
                CalendarEvent.objects.set_event_id(instance, self.feed,
                                                   new_event.id.text)
    
    def delete(self, sender, instance):
        """
        Delete the entry in Google Calendar corresponding to the given instance
        of the sender model type.
        """
        adapter = self.adapters[sender]
        if adapter.can_delete(instance):
            service = self.get_service()
            event = self.get_event(service, instance)
            if event:
                if adapter.can_notify(instance):
                    event.send_event_notifications = SendEventNotifications(
                        value='true')
                service.DeleteEvent(event.GetEditLink().href)
        CalendarEvent.objects.delete_event_id(instance, self.feed)
