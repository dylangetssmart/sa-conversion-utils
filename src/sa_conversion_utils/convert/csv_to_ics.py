import pandas as pd
from ics import Calendar, Event
from datetime import datetime
import uuid
# Load CSV
df = pd.read_csv("appointments.csv", encoding="windows-1252")
# Create calendar
calendar = Calendar()
# Helper to parse dates
def parse_datetime(dt_string):
    try:
        return datetime.strptime(dt_string.strip(), "%m/%d/%Y %I:%M:%S %p")
    except ValueError:
        return None
# Process each row
for _, row in df.iterrows():
    start_time = parse_datetime(row.get("Date and Time", ""))
    if not start_time:
        continue
    event = Event()
    event.name = str(row.get("Subject/Description", "Appointment"))
    event.begin = start_time
    event.uid = str(uuid.uuid4())
    desc_parts = [
        f"Staff: {row.get('Staff', '')}",
        f"Attending: {row.get('Attending', '')}",
        f"Case: {row.get('Case', '')}",
        f"Case Type: {row.get('Case Type', '')}",
        f"Assignee: {row.get('Assignee', '')}",
        f"Activity Type: {row.get('Activity Type', '')}",
        f"Description: {row.get('Description', '')}",
        f"Activity Info: {row.get('Activity Info', '')}"
    ]
    event.description = "\n".join(desc_parts)
    calendar.events.add(event)
# Write to .ics
with open("appointments.ics", "w") as f:
    f.writelines(calendar)