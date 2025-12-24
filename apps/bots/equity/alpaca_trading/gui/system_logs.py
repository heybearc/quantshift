"""
System Logs Dashboard Page
Displays comprehensive running logs from all system components.
"""

import streamlit as st
import os
import glob
from datetime import datetime, timedelta
import pandas as pd
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SystemLogsViewer:
    """System logs viewer for the dashboard."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.logs_dir = self.project_root / "logs"
        
    def show_logs_page(self):
        """Display the system logs page."""
        st.title("📋 System Logs")
        st.markdown("Complete running log of all system activities")
        
        # Create logs directory if it doesn't exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Sidebar controls
        with st.sidebar:
            st.header("Log Controls")
            
            # Log file selection
            log_files = self._get_available_log_files()
            
            # Debug information
            st.caption(f"Found {len(log_files)} log files")
            
            if log_files:
                # Show file sizes for context
                file_info = []
                for f in log_files[:5]:  # Show info for first 5 files
                    try:
                        file_path = self.logs_dir / f
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        file_info.append(f"{f} ({size_mb:.1f}MB)")
                    except:
                        file_info.append(f)
                
                selected_file = st.selectbox(
                    "Select Log File",
                    options=log_files,
                    index=0,
                    help="Choose which log file to display",
                    format_func=lambda x: f"{x} ({(self.logs_dir / x).stat().st_size / (1024 * 1024):.1f}MB)" if (self.logs_dir / x).exists() else x
                )
            else:
                st.warning("No log files found")
                selected_file = None
            
            # Time range filter
            st.subheader("Time Range")
            time_filter = st.radio(
                "Show logs from:",
                ["Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days", "All time"],
                index=2
            )
            
            # Log level filter
            st.subheader("Log Level")
            log_levels = st.multiselect(
                "Filter by level:",
                ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                default=["INFO", "WARNING", "ERROR", "CRITICAL"]
            )
            
            # Component filter
            st.subheader("Components")
            components = self._get_log_components(selected_file if selected_file else None)
            selected_components = st.multiselect(
                "Filter by component:",
                components,
                default=components[:5] if len(components) > 5 else components,
                help="Select which system components to show"
            )
            
            # Auto-refresh with proper timing
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
            
            # Manual refresh button
            if st.button("🔄 Refresh Now"):
                st.rerun()
            
            # Auto-refresh logic with session state to prevent constant rerunning
            if auto_refresh:
                import time
                current_time = time.time()
                
                # Initialize session state for auto-refresh timing
                if 'last_refresh_time' not in st.session_state:
                    st.session_state.last_refresh_time = current_time
                
                # Only refresh if 30 seconds have passed
                if current_time - st.session_state.last_refresh_time >= 30:
                    st.session_state.last_refresh_time = current_time
                    st.rerun()
                else:
                    # Show countdown
                    remaining = 30 - int(current_time - st.session_state.last_refresh_time)
                    st.caption(f"Next refresh in {remaining}s")
        
        # Main content area
        if selected_file:
            self._display_log_content(
                selected_file, 
                time_filter, 
                log_levels, 
                selected_components
            )
        else:
            # Show helpful information when no logs are available
            st.info("📋 No log files found")
            
            # Show logs directory status
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Logs Directory:** `{self.logs_dir}`")
                st.write(f"**Directory Exists:** {'✅ Yes' if self.logs_dir.exists() else '❌ No'}")
            
            with col2:
                if self.logs_dir.exists():
                    all_files = list(self.logs_dir.iterdir())
                    st.write(f"**Files in Directory:** {len(all_files)}")
                    if all_files:
                        st.write("**Files found:**")
                        for f in all_files[:5]:  # Show first 5 files
                            st.write(f"  • {f.name}")
            
            st.markdown("---")
            st.markdown("### 🚀 How to Generate Logs")
            st.markdown("""
            To see logs in this viewer, you can:
            
            1. **Run the test script** to generate sample logs:
               ```bash
               python3 scripts/test_logging.py
               ```
            
            2. **Run the screener** to generate real logs:
               ```bash
               python3 -m alpaca_trading.scripts.screener
               ```
            
            3. **Use the trading automation** which generates comprehensive logs:
               ```bash
               python3 -m alpaca_trading.scripts.daily_trading_automation
               ```
            
            Logs will automatically appear here once any system component runs.
            """)
            
        # Log statistics
        if selected_file:
            self._show_log_statistics(selected_file, time_filter)
    
    def _get_available_log_files(self):
        """Get list of available log files."""
        try:
            log_files = []
            
            # Check if logs directory exists
            if not self.logs_dir.exists():
                st.warning(f"Logs directory not found: {self.logs_dir}")
                return []
            
            # Look for all .log files in the logs directory
            for log_file in self.logs_dir.glob('*.log'):
                if log_file.is_file():
                    log_files.append(str(log_file))
            
            # Sort by modification time (newest first)
            if log_files:
                log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                # Return just the filenames
                return [os.path.basename(f) for f in log_files]
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error getting log files: {e}")
            st.error(f"Error accessing log files: {e}")
            return []
    
    def _get_log_components(self, log_file):
        """Extract unique component names from log file."""
        if not log_file:
            return []
            
        try:
            log_path = self.logs_dir / log_file
            components = set()
            
            # Read last 1000 lines to get recent components
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-1000:]
                
            for line in lines:
                # Extract component name from log format
                # Format: timestamp - component_name - level - message
                match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - ([^-]+) - \w+ - ', line)
                if match:
                    component = match.group(1).strip()
                    components.add(component)
            
            return sorted(list(components))
            
        except Exception as e:
            logger.error(f"Error extracting components: {e}")
            return []
    
    def _display_log_content(self, log_file, time_filter, log_levels, selected_components):
        """Display filtered log content."""
        try:
            log_path = self.logs_dir / log_file
            
            if not log_path.exists():
                st.error(f"Log file not found: {log_file}")
                return
            
            # Parse and filter logs
            log_entries = self._parse_log_file(log_path, time_filter, log_levels, selected_components)
            
            if not log_entries:
                st.info("No log entries match the current filters.")
                return
            
            # Display summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Entries", len(log_entries))
            with col2:
                error_count = sum(1 for entry in log_entries if entry['level'] in ['ERROR', 'CRITICAL'])
                st.metric("Errors", error_count)
            with col3:
                warning_count = sum(1 for entry in log_entries if entry['level'] == 'WARNING')
                st.metric("Warnings", warning_count)
            with col4:
                if log_entries:
                    latest_time = log_entries[0]['timestamp']
                    st.metric("Latest Entry", latest_time.strftime("%H:%M:%S"))
            
            st.markdown("---")
            
            # Display logs with color coding
            st.subheader(f"Log Entries ({len(log_entries)} entries)")
            
            # Create container for scrollable logs
            log_container = st.container()
            
            with log_container:
                for entry in log_entries[-500:]:  # Show last 500 entries
                    self._display_log_entry(entry)
                    
        except Exception as e:
            st.error(f"Error displaying logs: {e}")
            logger.error(f"Error in _display_log_content: {e}")
    
    def _parse_log_file(self, log_path, time_filter, log_levels, selected_components):
        """Parse log file and return filtered entries."""
        try:
            entries = []
            cutoff_time = self._get_cutoff_time(time_filter)
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Parse each line
            for line in lines:
                entry = self._parse_log_line(line.strip())
                if entry:
                    # Apply filters
                    if cutoff_time and entry['timestamp'] < cutoff_time:
                        continue
                    if entry['level'] not in log_levels:
                        continue
                    if selected_components and entry['component'] not in selected_components:
                        continue
                    
                    entries.append(entry)
            
            # Sort by timestamp (newest first)
            entries.sort(key=lambda x: x['timestamp'], reverse=True)
            return entries
            
        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
            return []
    
    def _parse_log_line(self, line):
        """Parse a single log line."""
        try:
            # Standard format: 2025-07-09 06:58:45,133 - alpaca_trading.scripts.screener - INFO - message
            pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - (\w+) - (.+)'
            match = re.match(pattern, line)
            
            if match:
                timestamp_str, component, level, message = match.groups()
                # Handle the microseconds format correctly
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                except ValueError:
                    # Fallback if microseconds parsing fails
                    timestamp_base = timestamp_str.split(',')[0]
                    timestamp = datetime.strptime(timestamp_base, "%Y-%m-%d %H:%M:%S")
                
                return {
                    'timestamp': timestamp,
                    'component': component.strip(),
                    'level': level.strip(),
                    'message': message.strip(),
                    'raw_line': line
                }
            
            # If regex doesn't match, try to extract at least some info
            if ' - ' in line:
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    try:
                        timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S,%f")
                    except:
                        timestamp = datetime.now()
                    
                    return {
                        'timestamp': timestamp,
                        'component': parts[1].strip(),
                        'level': parts[2].strip(),
                        'message': parts[3].strip(),
                        'raw_line': line
                    }
            
            return None
            
        except Exception as e:
            # If parsing fails, return a basic entry
            return {
                'timestamp': datetime.now(),
                'component': 'unknown',
                'level': 'INFO',
                'message': line,
                'raw_line': line
            }
    
    def _get_cutoff_time(self, time_filter):
        """Get cutoff time based on filter selection."""
        now = datetime.now()
        
        if time_filter == "Last 1 hour":
            return now - timedelta(hours=1)
        elif time_filter == "Last 6 hours":
            return now - timedelta(hours=6)
        elif time_filter == "Last 24 hours":
            return now - timedelta(days=1)
        elif time_filter == "Last 7 days":
            return now - timedelta(days=7)
        else:  # All time
            return None
    
    def _display_log_entry(self, entry):
        """Display a single log entry with formatting."""
        # Color coding based on log level
        level_colors = {
            'DEBUG': '#6c757d',      # Gray
            'INFO': '#17a2b8',       # Blue
            'WARNING': '#ffc107',    # Yellow
            'ERROR': '#dc3545',      # Red
            'CRITICAL': '#6f42c1'    # Purple
        }
        
        level_icons = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        color = level_colors.get(entry['level'], '#000000')
        icon = level_icons.get(entry['level'], '📝')
        
        # Format timestamp
        time_str = entry['timestamp'].strftime("%H:%M:%S")
        
        # Create expandable log entry
        with st.expander(
            f"{icon} {time_str} | {entry['component']} | {entry['level']} | {entry['message'][:100]}{'...' if len(entry['message']) > 100 else ''}",
            expanded=False
        ):
            st.markdown(f"""
            **Timestamp:** {entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")}  
            **Component:** {entry['component']}  
            **Level:** <span style="color: {color}; font-weight: bold;">{entry['level']}</span>  
            **Message:**
            ```
            {entry['message']}
            ```
            """, unsafe_allow_html=True)
    
    def _show_log_statistics(self, log_file, time_filter):
        """Show log statistics and charts."""
        try:
            st.markdown("---")
            st.subheader("📊 Log Statistics")
            
            log_path = self.logs_dir / log_file
            entries = self._parse_log_file(log_path, time_filter, 
                                         ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                                         [])
            
            if not entries:
                return
            
            # Create DataFrame for analysis
            df = pd.DataFrame(entries)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Log level distribution
                level_counts = df['level'].value_counts()
                st.bar_chart(level_counts)
                st.caption("Log Level Distribution")
            
            with col2:
                # Component activity
                component_counts = df['component'].value_counts().head(10)
                st.bar_chart(component_counts)
                st.caption("Top 10 Most Active Components")
            
            # Timeline chart (if we have enough data)
            if len(entries) > 10:
                # Group by hour
                df['hour'] = df['timestamp'].dt.floor('H')
                hourly_counts = df.groupby('hour').size()
                
                st.line_chart(hourly_counts)
                st.caption("Log Activity Over Time")
                
        except Exception as e:
            logger.error(f"Error showing log statistics: {e}")

def show_system_logs():
    """Main function to display system logs page."""
    viewer = SystemLogsViewer()
    viewer.show_logs_page()

if __name__ == "__main__":
    show_system_logs()
