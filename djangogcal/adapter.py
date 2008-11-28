"""
djangogcal.adapter


"""

from datetime import datetime

from atom import Content, Title
from gdata.calendar import When, Where, Who
from django.utils.tzinfo import FixedOffset, LocalTimezone

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

def format_datetime(date):
    """
    A utility method that converts the datetime to UTC serialized
    for Google Calendar.
    """
    local = date.replace(tzinfo=LocalTimezone(date))
    return local.astimezone(FixedOffset(0)).strftime(DATE_FORMAT)

class CalendarEventData(object):
    """
    A data-structure which converts Python data-types into Google Data API
    objects which can be transmitted to Google services.
    """
    
    def __init__(self, start, end, title="", where=None, who=None, content=""):
        """
        Instantiates a new instance of CalendarEventData.
        """
        self.start = start
        self.end = end
        self.title = title
        self.where = where or []
        self.who = who or []
        self.content = content
    
    def populate_event(self, event):
        """
        Populates the parameters of a Google Calendar event object.
        """
        event.when = [When(
            start_time=format_datetime(self.start),
            end_time=format_datetime(self.end)
        )]
        event.title = Title(text=self.title)
        event.where = [Where(value_string=x) for x in self.where]
        event.who = [Who(email=x) for x in self.who]
        event.content = Content(text=self.content)

class RawCalendarEventData(object):
    """
    A data-structure which accepts Google Calendar data types, for users who
    need access to advanced fields.
    """
    
    def __init__(self, when, **kwargs):
        """
        Instantiates a new instance of RawCalendarEventData.
        """
        self.when = when
        self.kwargs = kwargs
    
    def populate_event(self, event):
        """
        Populates the parameters of a Google Calendar event object.
        """
        event.when = self.when
        for key in self.kwargs:
            setattr(event, key, self.kwargs[key])

class CalendarAdapter(object):
    """
    
    """
    
    def __init__(self):
        """
        Instantiates a new instance of CalendarAdapter.
        """
        pass
    
    def can_save(self, instance):
        """
        Should return a boolean indicating whether the object can be stored or
        updated in Google Calendar.
        """
        return True
    
    def can_delete(self, instance):
        """
        Should return a boolean indicating whether the object can be deleted
        from Google Calendar.
        """
        return True

    def can_notify(self, instance):
        """
        Should return a boolean indicating whether Google Calendar should send
        event change notifications.
        """
        return False
    
    def get_event_data(self, instance):
        """
        This method should be implemented by users, and must return an object
        conforming to the CalendarEventData protocol.
        """
        raise NotImplementedError()
