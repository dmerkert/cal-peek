# iCal Upcoming Events Parser

A Python tool that reads iCal data from stdin and displays upcoming events within the next 7 days, with proper support for recurring events.

## Features

- Reads iCal data via Linux pipes (stdin)
- Shows events for the next 7 days (configurable)
- Handles recurring events (RRULE) correctly
- Timezone aware
- Packaged as a Nix Flake for easy deployment

## Usage

### With Nix Flake

```bash
# Run directly from GitHub
nix run github:dmerkert/cal-peek -- --help

# Or with calendar data
cat calendar.ics | nix run github:dmerkert/cal-peek

# Run directly with a file (local development)
cat calendar.ics | nix run .

# Run with URL
curl -s https://example.com/calendar.ics | nix run .

# Run with custom timeframe (14 days)
cat calendar.ics | nix run . -- --days 14

# Enter development shell
nix develop

# Run tests
nix run .#test

# Run tests with coverage
nix run .#test-cov
```

### Direct Python Usage

```bash
# Install dependencies first
pip install icalendar python-dateutil pytz

# Run the script
cat calendar.ics | python ical_upcoming.py

# With options
cat calendar.ics | python ical_upcoming.py --days 14
```

## Command Line Options

- `--days, -d`: Number of days to look ahead (default: 7)
- `--format, -f`: Output format - `simple` or `detailed` (default: simple)

## Development

This project uses Test-Driven Development (TDD). The test suite includes:

- Unit tests for iCal parsing
- Tests for recurring event expansion
- Tests for timezone handling
- Integration tests for pipe functionality

### Running Tests

```bash
# In development shell
pytest tests/ -v

# With coverage
pytest tests/ --cov=ical_upcoming --cov-report=html
```

### Test Files

The `tests/fixtures/` directory contains sample iCal files for testing:

- `simple_events.ics` - Basic non-recurring events
- `recurring_events.ics` - Events with RRULE patterns
- `timezone_events.ics` - Events with timezone information
- `mixed_events.ics` - Mixed scenarios for edge case testing

## Implementation Details

- Uses `icalendar` library for parsing iCal data
- Uses `python-dateutil` for recurring event expansion
- Handles timezone conversion with `pytz`
- Sorts events by start time
- Filters events within the specified date range

## Example Output

```
Upcoming events in the next 7 days:
--------------------------------------------------
2025-07-03 10:00-11:00: Team Meeting - Weekly team sync
2025-07-03 09:00-09:30: Daily Standup - Daily team standup
2025-07-04 09:00-09:30: Daily Standup - Daily team standup
2025-07-05 14:00-15:00: Doctor Appointment - Regular checkup
```