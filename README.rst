==========
djangogcal
==========

Usage
=====

In a typical scenario, the following steps are required to use django-gcal:

Add djangogcal to the list of installed applications in your settings.py.
Define a djangogcal.adapter.CalendarAdapter for each model you want synchronised.
Instantiate a djangogcal.observer.CalendarObserver for each Google Calendar feed.
Call the CalendarObserver.observe(model, adapter) method to link models with the Google Calendar feed.
See GettingStarted for more information, and RelatedModels for information about sending updates when related objects are changed.

Example
=======

The code in this example is sufficient to bind a model to Google Calendar::

    from django.conf import settings

    from djangogcal.adapter import CalendarAdapter, CalendarEventData
    from djangogcal.observer import CalendarObserver

    from models import Showing

    class ShowingCalendarAdapter(CalendarAdapter):
        """
        A calendar adapter for the Showing model.
        """
        
        def get_event_data(self, instance):
            """
            Returns a CalendarEventData object filled with data from the adaptee.
            """
            return CalendarEventData(
                start=instance.start_time,
                end=instance.end_time,
                title=instance.title
            )

    observer = CalendarObserver(email=settings.CALENDAR_EMAIL,
                                password=settings.CALENDAR_PASSWORD)
    observer.observe(Showing, ShowingCalendarAdapter())

