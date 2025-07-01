#!/usr/bin/env python3
"""
iCal Upcoming Events Parser

Reads iCal data from stdin and outputs events occurring in the next 7 days,
including proper handling of recurring events.
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
from icalendar import Calendar, Event
from dateutil.rrule import rrulestr
from dateutil.parser import parse as parse_date


class ICalParser:
    """Parser for iCal calendar data"""
    
    def __init__(self):
        self.timezone = pytz.UTC
    
    def parse(self, ical_data: str) -> List[Event]:
        """Parse iCal data and return list of events"""
        if not ical_data.strip():
            return []
        
        try:
            calendar = Calendar.from_ical(ical_data)
        except Exception as e:
            raise ValueError(f"Invalid iCal data: {e}")
        
        events = []
        for component in calendar.walk():
            if component.name == "VEVENT":
                events.append(component)
        
        return events


def get_upcoming_events(ical_data: str, reference_date: Optional[datetime] = None, days: int = 7) -> List[Dict[str, Any]]:
    """
    Get events occurring within the specified number of days from reference date.
    
    Args:
        ical_data: iCal format string
        reference_date: Reference date (defaults to now)
        days: Number of days to look ahead (default: 7)
    
    Returns:
        List of event dictionaries with 'summary', 'start', 'end', 'description'
    """
    if not ical_data.strip():
        return []
    
    if reference_date is None:
        reference_date = datetime.now(pytz.UTC)
    elif reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=pytz.UTC)
    
    parser = ICalParser()
    events = parser.parse(ical_data)
    
    upcoming_events = []
    end_date = reference_date + timedelta(days=days)
    
    for event in events:
        event_occurrences = _get_event_occurrences(event, reference_date, end_date)
        upcoming_events.extend(event_occurrences)
    
    # Sort by start time
    upcoming_events.sort(key=lambda x: x['start'])
    
    return upcoming_events


def _get_event_occurrences(event: Event, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get all occurrences of an event (including recurring) within date range"""
    occurrences = []
    
    # Get basic event info
    summary = str(event.get('summary', 'No Title'))
    description = str(event.get('description', ''))
    
    # Parse start and end times
    event_start = event.get('dtstart')
    event_end = event.get('dtend')
    
    if not event_start:
        return []
    
    # Handle different datetime formats
    if hasattr(event_start, 'dt'):
        start_dt = event_start.dt
        if hasattr(event_end, 'dt'):
            end_dt = event_end.dt
        else:
            # If no end time, assume 1 hour duration
            end_dt = start_dt + timedelta(hours=1)
    else:
        start_dt = event_start
        end_dt = event_end if event_end else start_dt + timedelta(hours=1)
    
    # Ensure timezone awareness
    if isinstance(start_dt, datetime):
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=pytz.UTC)
        if isinstance(end_dt, datetime) and end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=pytz.UTC)
    
    # Handle recurring events
    rrule = event.get('rrule')
    if rrule:
        # Parse RRULE
        rrule_str = rrule.to_ical().decode('utf-8')
        
        try:
            # Create rrule with proper start date
            rule = rrulestr(rrule_str, dtstart=start_dt)
            
            # Get occurrences within date range
            for occurrence_start in rule:
                if occurrence_start > end_date:
                    break
                if occurrence_start >= start_date:
                    # Calculate duration
                    if isinstance(end_dt, datetime) and isinstance(start_dt, datetime):
                        duration = end_dt - start_dt
                        occurrence_end = occurrence_start + duration
                    else:
                        occurrence_end = occurrence_start + timedelta(hours=1)
                    
                    occurrences.append({
                        'summary': summary,
                        'start': occurrence_start,
                        'end': occurrence_end,
                        'description': description
                    })
        except Exception:
            # If RRULE parsing fails, treat as single event
            pass
    
    # Handle single occurrence (non-recurring or fallback)
    if not rrule or not occurrences:
        if isinstance(start_dt, datetime):
            if start_date <= start_dt <= end_date:
                occurrences.append({
                    'summary': summary,
                    'start': start_dt,
                    'end': end_dt if isinstance(end_dt, datetime) else start_dt + timedelta(hours=1),
                    'description': description
                })
    
    return occurrences


def format_event(event: Dict[str, Any], format_type: str = 'simple'):
    """Format an event for display"""
    if format_type == 'detailed':
        return _format_event_detailed(event)
    elif format_type == 'json':
        return _format_event_json(event)
    else:
        return _format_event_simple(event)


def _format_event_simple(event: Dict[str, Any]) -> str:
    """Format an event in simple format (original format)"""
    start_time = event['start'].strftime('%Y-%m-%d %H:%M')
    end_time = event['end'].strftime('%H:%M')
    
    output = f"{start_time}-{end_time}: {event['summary']}"
    if event['description']:
        output += f" - {event['description']}"
    
    return output


def _format_event_detailed(event: Dict[str, Any]) -> str:
    """Format an event in detailed format showing all properties"""
    lines = []
    
    # Title
    lines.append(f"Title: {event['summary']}")
    
    # Date and time
    start_dt = event['start']
    end_dt = event['end']
    
    # Same day event
    if start_dt.date() == end_dt.date():
        lines.append(f"Date: {start_dt.strftime('%Y-%m-%d')}")
        lines.append(f"Time: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")
    else:
        # Multi-day event
        lines.append(f"Start: {start_dt.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"End: {end_dt.strftime('%Y-%m-%d %H:%M')}")
    
    # Duration
    duration = end_dt - start_dt
    if duration.days > 0:
        lines.append(f"Duration: {duration.days} days, {duration.seconds // 3600} hours, {(duration.seconds % 3600) // 60} minutes")
    else:
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        if hours > 0:
            lines.append(f"Duration: {hours} hours, {minutes} minutes")
        else:
            lines.append(f"Duration: {minutes} minutes")
    
    # Description (only if not empty)
    if event['description'] and event['description'].strip():
        lines.append(f"Description: {event['description']}")
    
    return '\n'.join(lines)


def _format_event_json(event: Dict[str, Any]) -> Dict[str, Any]:
    """Format an event as JSON-serializable dictionary"""
    # Calculate duration in minutes
    duration = event['end'] - event['start']
    duration_minutes = int(duration.total_seconds() / 60)
    
    return {
        'summary': event['summary'],
        'start': event['start'].isoformat(),
        'end': event['end'].isoformat(),
        'description': event['description'],
        'duration_minutes': duration_minutes
    }


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(
        description='Show upcoming events from iCal data piped via stdin'
    )
    parser.add_argument(
        '--days', '-d', 
        type=int, 
        default=7, 
        help='Number of days to look ahead (default: 7)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['simple', 'detailed', 'json'],
        default='simple',
        help='Output format: simple, detailed, or json (default: simple)'
    )
    
    args = parser.parse_args()
    
    # Read from stdin
    try:
        ical_data = sys.stdin.read()
    except KeyboardInterrupt:
        sys.exit(0)
    
    if not ical_data.strip():
        print("No iCal data provided via stdin", file=sys.stderr)
        sys.exit(1)
    
    try:
        events = get_upcoming_events(ical_data, days=args.days)
        
        if not events:
            if args.format == 'json':
                print(json.dumps({
                    "events": [],
                    "metadata": {
                        "days_ahead": args.days,
                        "total_events": 0
                    }
                }, indent=2))
            else:
                print(f"No events found in the next {args.days} days")
            return
        
        if args.format == 'json':
            # Format all events as JSON
            json_events = [format_event(event, format_type='json') for event in events]
            output = {
                "events": json_events,
                "metadata": {
                    "days_ahead": args.days,
                    "total_events": len(events)
                }
            }
            print(json.dumps(output, indent=2))
        else:
            # Text format output
            print(f"Upcoming events in the next {args.days} days:")
            print("-" * 50)
            
            for i, event in enumerate(events):
                if i > 0 and args.format == 'detailed':
                    print()  # Add blank line between detailed appointments
                    print("=" * 50)  # Add separator line
                    print()
                print(format_event(event, format_type=args.format))
            
    except ValueError as e:
        print(f"Error parsing iCal data: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()