import pytest
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
import pytz

# Add src to path for importing our module
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ical_upcoming import ICalParser, get_upcoming_events
except ImportError:
    # Module doesn't exist yet - that's expected in TDD
    pass


class TestICalParser:
    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"
    
    @pytest.fixture
    def simple_ical(self, fixtures_path):
        return (fixtures_path / "simple_events.ics").read_text()
    
    @pytest.fixture
    def recurring_ical(self, fixtures_path):
        return (fixtures_path / "recurring_events.ics").read_text()
    
    @pytest.fixture
    def timezone_ical(self, fixtures_path):
        return (fixtures_path / "timezone_events.ics").read_text()
    
    @pytest.fixture
    def mixed_ical(self, fixtures_path):
        return (fixtures_path / "mixed_events.ics").read_text()

    def test_parser_can_be_instantiated(self):
        """Test that ICalParser can be created"""
        parser = ICalParser()
        assert parser is not None

    def test_parse_simple_events(self, simple_ical):
        """Test parsing simple non-recurring events"""
        parser = ICalParser()
        events = parser.parse(simple_ical)
        
        assert len(events) == 3
        assert any("Team Meeting" in str(event) for event in events)
        assert any("Doctor Appointment" in str(event) for event in events)
        assert any("Gym Session" in str(event) for event in events)

    def test_get_events_within_7_days(self, mixed_ical):
        """Test filtering events within the next 7 days"""
        # Mock current date to 2025-07-01
        reference_date = datetime(2025, 7, 1, tzinfo=pytz.UTC)
        
        events = get_upcoming_events(mixed_ical, reference_date=reference_date, days=7)
        
        # Should only include events within 7 days from reference_date
        # Past events and events > 7 days should be excluded
        event_summaries = [event['summary'] for event in events]
        
        assert "Past Event" not in event_summaries
        assert "Future Event" not in event_summaries
        assert "Within 7 Days" in event_summaries

    def test_get_events_with_default_timeframe(self, simple_ical):
        """Test that default timeframe is 7 days from now"""
        events = get_upcoming_events(simple_ical)
        
        # Should return events (exact number depends on current date)
        assert isinstance(events, list)

    def test_parse_recurring_events(self, recurring_ical):
        """Test parsing and expanding recurring events"""
        reference_date = datetime(2025, 7, 1, tzinfo=pytz.UTC)
        
        events = get_upcoming_events(recurring_ical, reference_date=reference_date, days=7)
        
        # Should expand recurring events within the 7-day window
        daily_events = [e for e in events if "Daily Standup" in e['summary']]
        weekly_events = [e for e in events if "Weekly Review" in e['summary']]
        
        # Daily standup should have multiple occurrences in 7 days
        assert len(daily_events) >= 7  # At least 7 daily occurrences
        # Weekly review on Tuesday (2025-07-02 is Wednesday, so next Tuesday is in range)
        assert len(weekly_events) >= 1

    def test_timezone_handling(self, timezone_ical):
        """Test proper timezone handling"""
        reference_date = datetime(2025, 7, 1, tzinfo=pytz.UTC)
        
        events = get_upcoming_events(timezone_ical, reference_date=reference_date, days=7)
        
        # Should handle both timezone-aware and UTC events
        assert len(events) >= 1
        
        # Events should have proper datetime objects
        for event in events:
            assert isinstance(event['start'], datetime)
            assert event['start'].tzinfo is not None

    def test_empty_input(self):
        """Test handling of empty input"""
        events = get_upcoming_events("")
        assert events == []

    def test_invalid_ical_input(self):
        """Test handling of invalid iCal data"""
        invalid_ical = "This is not valid iCal data"
        
        with pytest.raises(ValueError):
            get_upcoming_events(invalid_ical)

    def test_event_output_format(self, simple_ical):
        """Test that events have required fields"""
        events = get_upcoming_events(simple_ical)
        
        if events:  # Only test if we have events
            event = events[0]
            
            # Each event should have these fields
            required_fields = ['summary', 'start', 'end', 'description']
            for field in required_fields:
                assert field in event
            
            # Start should be before end
            assert event['start'] < event['end']

    def test_events_sorted_by_start_time(self, mixed_ical):
        """Test that events are returned sorted by start time"""
        reference_date = datetime(2025, 7, 1, tzinfo=pytz.UTC)
        events = get_upcoming_events(mixed_ical, reference_date=reference_date, days=7)
        
        if len(events) > 1:
            for i in range(len(events) - 1):
                assert events[i]['start'] <= events[i + 1]['start']


class TestStdinPipeIntegration:
    """Test reading from stdin pipe"""
    
    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"
    
    @pytest.fixture
    def simple_ical(self, fixtures_path):
        return (fixtures_path / "simple_events.ics").read_text()
    
    def test_read_from_stdin(self, simple_ical, monkeypatch):
        """Test reading iCal data from stdin"""
        # Mock stdin
        fake_stdin = StringIO(simple_ical)
        monkeypatch.setattr(sys, 'stdin', fake_stdin)
        
        # This test will be implemented when we have the main function
        # For now, just test that we can mock stdin
        content = sys.stdin.read()
        assert "BEGIN:VCALENDAR" in content

    def test_pipe_integration_with_cat(self, fixtures_path):
        """Integration test using subprocess to simulate pipe"""
        import subprocess
        
        # This will test the actual pipe functionality once implemented
        # For now, just ensure the test files exist
        simple_file = fixtures_path / "simple_events.ics"
        assert simple_file.exists()


class TestFormatting:
    """Test event formatting functionality"""
    
    @pytest.fixture
    def sample_event(self):
        """Sample event for testing formatting"""
        return {
            'summary': 'Team Meeting',
            'start': datetime(2025, 7, 3, 10, 0, tzinfo=pytz.UTC),
            'end': datetime(2025, 7, 3, 11, 0, tzinfo=pytz.UTC),
            'description': 'Weekly team sync meeting'
        }
    
    @pytest.fixture
    def event_no_description(self):
        """Sample event without description"""
        return {
            'summary': 'Quick Call',
            'start': datetime(2025, 7, 3, 14, 0, tzinfo=pytz.UTC), 
            'end': datetime(2025, 7, 3, 14, 30, tzinfo=pytz.UTC),
            'description': ''
        }
    
    def test_format_event_function_exists(self):
        """Test that format_event function exists"""
        try:
            from ical_upcoming import format_event
            assert callable(format_event)
        except ImportError:
            pytest.skip("format_event function not implemented yet")
    
    def test_simple_format_output(self, sample_event):
        """Test simple format produces expected output"""
        try:
            from ical_upcoming import format_event
            
            result = format_event(sample_event, format_type='simple')
            
            # Should contain time range and summary
            assert '2025-07-03 10:00-11:00' in result
            assert 'Team Meeting' in result
            assert 'Weekly team sync meeting' in result
        except ImportError:
            pytest.skip("format_event function not implemented yet")
    
    def test_detailed_format_shows_more_info(self, sample_event):
        """Test detailed format shows more information than simple"""
        try:
            from ical_upcoming import format_event
            
            simple_result = format_event(sample_event, format_type='simple')
            detailed_result = format_event(sample_event, format_type='detailed')
            
            # Detailed should be longer and contain more information
            assert len(detailed_result) > len(simple_result)
            assert 'Team Meeting' in detailed_result
            assert 'Weekly team sync meeting' in detailed_result
            
            # Detailed should show more formatted information
            assert detailed_result != simple_result
        except ImportError:
            pytest.skip("format_event function not implemented yet")
    
    def test_detailed_format_structure(self, sample_event):
        """Test detailed format has proper structure with all fields"""
        try:
            from ical_upcoming import format_event
            
            result = format_event(sample_event, format_type='detailed')
            
            # Should contain all event information in detailed format
            assert 'Team Meeting' in result
            assert '2025-07-03' in result  # Date
            assert '10:00' in result       # Start time
            assert '11:00' in result       # End time
            assert 'Weekly team sync meeting' in result  # Description
            
            # Should be multiline for detailed view
            assert '\n' in result
        except ImportError:
            pytest.skip("format_event function not implemented yet")
    
    def test_detailed_format_handles_empty_description(self, event_no_description):
        """Test detailed format handles events without description"""
        try:
            from ical_upcoming import format_event
            
            result = format_event(event_no_description, format_type='detailed')
            
            # Should still work without description
            assert 'Quick Call' in result
            assert '2025-07-03' in result
            # Should not show empty description line
            assert 'Description:' not in result or 'Description: \n' not in result
        except ImportError:
            pytest.skip("format_event function not implemented yet")
    
    def test_format_event_backward_compatibility(self, sample_event):
        """Test format_event works without format_type parameter (default simple)"""
        try:
            from ical_upcoming import format_event
            
            # Should default to simple format if no format_type specified
            result_default = format_event(sample_event)
            result_simple = format_event(sample_event, format_type='simple')
            
            assert result_default == result_simple
        except ImportError:
            pytest.skip("format_event function not implemented yet")

    def test_format_event_json(self, sample_event):
        """Test format_event returns JSON-serializable dict for json format"""
        try:
            from ical_upcoming import format_event
            import json
            
            result = format_event(sample_event, format_type='json')
            
            # Should return a dictionary
            assert isinstance(result, dict)
            
            # Should have required fields
            assert 'summary' in result
            assert 'start' in result
            assert 'end' in result
            assert 'description' in result
            assert 'duration_minutes' in result
            
            # Should be JSON-serializable
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
            
            # Verify content
            assert result['summary'] == sample_event['summary']
            assert result['description'] == sample_event['description']
            assert isinstance(result['duration_minutes'], int)
            
        except ImportError:
            pytest.skip("format_event function not implemented yet")


class TestMainFunction:
    """Test the main entry point function"""
    
    def test_main_function_exists(self):
        """Test that main function exists and can be called"""
        try:
            from ical_upcoming import main
            assert callable(main)
        except ImportError:
            pytest.skip("main function not implemented yet")

    def test_main_with_args(self):
        """Test main function with command line arguments"""
        try:
            from ical_upcoming import main
            # Test will be implemented once main function exists
            pass
        except ImportError:
            pytest.skip("main function not implemented yet")