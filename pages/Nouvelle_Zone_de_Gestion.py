from streamlit_calendar import calendar
import streamlit as st


calendar_events = [
    {
        "title": "Event 1",
        "start": "2024-08-12T08:30:00",
        "resourceId": "a",
        "backgroundColor": "red",
        "classNames": ["fc-event-past", "fc-event-time"],
    },
    {
        "title": "Event 2",
        "start": "2024-08-12T07:30:00",
        "end": "2024-08-12T10:30:00",
        "resourceId": "b",
    },
    {
        "title": "Event 3",
        "start": "2023-07-31T10:40:00",
        "end": "2023-07-31T12:30:00",
        "resourceId": "a",
    },
]
custom_css = """
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: 700;
    }
    .fc-toolbar-title {
        font-size: 2rem;
    }
"""

calendar = calendar(events=calendar_events, custom_css=custom_css)
st.write(calendar)
