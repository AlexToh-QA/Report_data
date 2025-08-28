import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_time_to_hour(time_str):
    """Parse time string and extract hour"""
    try:
        time_str = str(time_str).strip()

        # Handle hour format like "11 AM", "12 PM", "1 PM", "2 PM"
        if 'AM' in time_str.upper() or 'PM' in time_str.upper():
            # Extract hour from formats like "11 AM", "12 PM"
            parts = time_str.upper().replace('AM', '').replace('PM', '').strip()
            hour = int(parts)
            if 'PM' in time_str.upper() and hour != 12:
                hour += 12
            elif 'AM' in time_str.upper() and hour == 12:
                hour = 0
            return hour

        # Handle different date formats
        formats = [
            '%m/%d/%Y %H:%M',  # 07/30/2025 11:03
            '%Y-%m-%d %H:%M:%S',  # 2025-07-30 11:03:00
            '%Y-%m-%d %H:%M',  # 2025-07-30 11:03
            '%m/%d/%Y %H:%M:%S',  # 07/30/2025 11:03:00
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.hour
            except ValueError:
                continue

        # If none of the formats work, try pandas to_datetime
        dt = pd.to_datetime(time_str)
        return dt.hour
    except:
        return None

def parse_operating_hours(operating_hours_str):
    """Parse operating hours string (HH:MM format) and return hour as integer"""
    try:
        if not operating_hours_str or operating_hours_str.strip() == '':
            return 0  # Default to midnight

        # Parse time string like "05:00" or "17:30"
        time_obj = datetime.strptime(operating_hours_str.strip(), '%H:%M')
        return time_obj.hour
    except:
        return 0  # Default to midnight if parsing fails

def get_business_date(dt, operating_start_hour=0):
    """
    Get the business date for a given datetime based on operating hours.

    Args:
        dt: datetime object
        operating_start_hour: Hour when business day starts (0-23)

    Returns:
        date object representing the business date

    Example:
        If operating_start_hour = 5 (5:00 AM):
        - 2025-05-16 01:00 -> business date: 2025-05-15 (still previous business day)
        - 2025-05-16 06:00 -> business date: 2025-05-16 (new business day started)
    """
    if dt.hour < operating_start_hour:
        # Before operating hours start, belongs to previous business day
        return (dt.date() - timedelta(days=1))
    else:
        # After operating hours start, belongs to current business day
        return dt.date()

def parse_time_to_date(time_str, operating_start_hour=0):
    """Parse time string and extract business date based on operating hours"""
    try:
        time_str = str(time_str).strip()

        # Handle different date formats
        formats = [
            '%m/%d/%Y %H:%M',  # 07/30/2025 11:03
            '%Y-%m-%d %H:%M:%S',  # 2025-07-30 11:03:00
            '%Y-%m-%d %H:%M',  # 2025-07-30 11:03
            '%m/%d/%Y %H:%M:%S',  # 07/30/2025 11:03:00
            '%m/%d/%Y',  # 07/30/2025
            '%Y-%m-%d',  # 2025-07-30
            '%d %b %Y (%a)',  # 22 Aug 2025 (Fri)
            '%d %b %Y',  # 22 Aug 2025
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return get_business_date(dt, operating_start_hour)
            except ValueError:
                continue

        # If none of the formats work, try pandas to_datetime
        dt = pd.to_datetime(time_str)
        return get_business_date(dt, operating_start_hour)
    except:
        return None

def parse_report_date(time_str):
    """Parse report date string - for dates that are already business dates (no operating hours adjustment)"""
    try:
        time_str = str(time_str).strip()

        # Handle different date formats - these are already business dates
        formats = [
            '%d %b %Y (%a)',  # 22 Aug 2025 (Fri) - common in report CSVs
            '%d %b %Y',  # 22 Aug 2025
            '%m/%d/%Y',  # 07/30/2025
            '%Y-%m-%d',  # 2025-07-30
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.date()  # Return date directly without operating hours adjustment
            except ValueError:
                continue

        # If none of the formats work, try pandas to_datetime
        dt = pd.to_datetime(time_str)
        return dt.date()
    except:
        return None

def process_offline_csv(file_path, view_type='hourly', operating_start_hour=0):
    """Process offline CSV file according to filtering rules"""
    try:
        df = pd.read_csv(file_path)

        # Debug: Print column names and sample data
        print(f"Offline CSV columns: {list(df.columns)}")
        print(f"Sample Transaction Type values: {df['Transaction Type'].unique()[:5]}")
        print(f"Sample Is_Cancelled values: {df['Is_Cancelled'].unique()[:5]}")

        # Handle string boolean values for Is_Cancelled
        df['Is_Cancelled_Bool'] = df['Is_Cancelled'].astype(str).str.upper().isin(['TRUE', 'T', '1', 'YES'])

        # Filter: Transaction Type = Sale and Is_Cancelled = False
        filtered_df = df[
            (df['Transaction Type'].str.strip().str.lower() == 'sale') &
            (df['Is_Cancelled_Bool'] == False)
        ].copy()

        print(f"Filtered offline rows: {len(filtered_df)} out of {len(df)}")

        if len(filtered_df) == 0:
            if view_type == 'daily':
                return pd.Series(dtype=float)  # Empty series for daily view
            else:
                return pd.Series(0.0, index=range(24))  # Empty hourly series

        if view_type == 'daily':
            # Extract business date from Time column using operating hours
            filtered_df['Date'] = filtered_df['Time'].apply(lambda x: parse_time_to_date(x, operating_start_hour))

            # Remove rows where date parsing failed
            filtered_df = filtered_df.dropna(subset=['Date'])

            print(f"Offline rows after date parsing: {len(filtered_df)}")

            # Group by date and sum Total column
            daily_totals = filtered_df.groupby('Date')['Total'].sum()
            return daily_totals
        else:
            # Extract hour from Time column
            filtered_df['Hour'] = filtered_df['Time'].apply(parse_time_to_hour)

            # Remove rows where hour parsing failed
            filtered_df = filtered_df.dropna(subset=['Hour'])

            print(f"Offline rows after time parsing: {len(filtered_df)}")

            # Group by hour and sum Total column
            hourly_totals = filtered_df.groupby('Hour')['Total'].sum()

            # Create series for all 24 hours (0-23)
            result = pd.Series(0.0, index=range(24))
            result.update(hourly_totals)

            return result

    except Exception as e:
        raise Exception(f"Error processing offline CSV: {str(e)}")

def process_online_csv(file_path, view_type='hourly', operating_start_hour=0):
    """Process online CSV file according to filtering rules"""
    try:
        df = pd.read_csv(file_path)

        # Debug: Print column names and sample data
        print(f"Online CSV columns: {list(df.columns)}")
        print(f"All Status values: {df['Status'].value_counts()}")

        # Filter: Exclude "Pending Store Acceptance", "Cancelled", and "Pending Payment"
        excluded_statuses = ['pending store acceptance', 'cancelled', 'pending payment']

        filtered_df = df[
            ~df['Status'].str.strip().str.lower().isin(excluded_statuses)
        ].copy()

        print(f"Filtered online rows: {len(filtered_df)} out of {len(df)}")
        print(f"Excluded statuses: {excluded_statuses}")

        if len(filtered_df) > 0:
            print("Included statuses in filtered data:")
            print(filtered_df['Status'].value_counts())
        else:
            print("No online transactions match the filter criteria")
            if view_type == 'daily':
                return pd.Series(dtype=float)  # Empty series for daily view
            else:
                return pd.Series(0.0, index=range(24))  # Empty hourly series

        if view_type == 'daily':
            # Extract business date from Created Time column using operating hours
            filtered_df['Date'] = filtered_df['Created Time'].apply(lambda x: parse_time_to_date(x, operating_start_hour))

            # Remove rows where date parsing failed
            filtered_df = filtered_df.dropna(subset=['Date'])

            print(f"Online rows after date parsing: {len(filtered_df)}")

            # Group by date and sum Total column
            daily_totals = filtered_df.groupby('Date')['Total'].sum()
            return daily_totals
        else:
            # Extract hour from Created Time column
            filtered_df['Hour'] = filtered_df['Created Time'].apply(parse_time_to_hour)

            # Remove rows where hour parsing failed
            filtered_df = filtered_df.dropna(subset=['Hour'])

            print(f"Online rows after time parsing: {len(filtered_df)}")

            if len(filtered_df) == 0:
                print("No valid time data found in online CSV")
                return pd.Series(0.0, index=range(24))

            # Group by hour and sum Total column
            hourly_totals = filtered_df.groupby('Hour')['Total'].sum()

            print(f"Online hourly totals calculated: {hourly_totals.sum():.2f}")

            # Create series for all 24 hours (0-23)
            result = pd.Series(0.0, index=range(24))
            result.update(hourly_totals)

            return result

    except Exception as e:
        raise Exception(f"Error processing online CSV: {str(e)}")

def process_report_csv(file_path, view_type='hourly', operating_start_hour=0):
    """Process report CSV file and extract hourly or daily data"""
    try:
        df = pd.read_csv(file_path)

        # Debug: Print column names and sample data
        print(f"Report CSV columns: {list(df.columns)}")
        print(f"Sample report data (first 3 rows):")
        print(df.head(3))

        # Try to identify the datetime and value columns
        datetime_col = None
        value_col = None

        # Look for common datetime column names
        datetime_candidates = ['datetime', 'date_time', 'time', 'timestamp', 'created_time', 'date', 'date / time']
        for col in df.columns:
            if col.lower().strip() in datetime_candidates or 'time' in col.lower() or 'date' in col.lower():
                datetime_col = col
                break

        # Look for common value column names
        value_candidates = ['total', 'amount', 'value', 'sum', 'revenue', 'total sales', 'sales']
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in value_candidates or 'total' in col_lower or 'sales' in col_lower:
                value_col = col
                break

        # If not found, use the first two columns
        if datetime_col is None:
            datetime_col = df.columns[0]
        if value_col is None:
            value_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        print(f"Using datetime column: {datetime_col}")
        print(f"Using value column: {value_col}")

        if view_type == 'daily':
            # For report CSV, use parse_report_date (no operating hours adjustment)
            # Report dates are already business dates, not timestamps
            df['Date'] = df[datetime_col].apply(parse_report_date)

            # Remove rows where date parsing failed
            df = df.dropna(subset=['Date'])

            print(f"Report rows after date parsing: {len(df)}")

            # Group by date and sum values
            daily_totals = df.groupby('Date')[value_col].sum()

            print(f"Report daily totals calculated: {daily_totals.sum():.2f}")

            return daily_totals
        else:
            # Extract hour from datetime column
            df['Hour'] = df[datetime_col].apply(parse_time_to_hour)

            # Remove rows where hour parsing failed
            df = df.dropna(subset=['Hour'])

            print(f"Report rows after time parsing: {len(df)}")

            # Group by hour and sum values
            hourly_totals = df.groupby('Hour')[value_col].sum()

            # Create series for all 24 hours (0-23)
            result = pd.Series(0.0, index=range(24))
            result.update(hourly_totals)

            print(f"Report hourly totals calculated: {result.sum():.2f}")

            return result

    except Exception as e:
        raise Exception(f"Error processing report CSV: {str(e)}")

def format_hour_label(hour):
    """Convert hour (0-23) to readable format"""
    if hour == 0:
        return "12 AM"
    elif hour < 12:
        return f"{hour:02d} AM"
    elif hour == 12:
        return "12 PM"
    else:
        return f"{hour-12:02d} PM"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get uploaded files
        online_file = request.files.get('online_csv')
        offline_file = request.files.get('offline_csv')
        report_file = request.files.get('report_csv')

        # Get view selection (default to hourly for backward compatibility)
        view_type = request.form.get('view_type', 'hourly')
        print(f"Selected view type: {view_type}")

        # Get operating hours (default to 00:00 if not provided)
        operating_hours_str = request.form.get('operating_hours', '00:00')
        operating_start_hour = parse_operating_hours(operating_hours_str)
        print(f"Operating hours: {operating_hours_str} -> Start hour: {operating_start_hour}")

        # Validate that at least one file is uploaded
        if not online_file and not offline_file:
            flash('Please upload at least one CSV file (Online or Offline).', 'error')
            return redirect(url_for('index'))

        # Validate file extensions for uploaded files
        files_to_check = []
        if online_file:
            files_to_check.append(online_file)
        if offline_file:
            files_to_check.append(offline_file)
        if report_file:
            files_to_check.append(report_file)

        if not all(allowed_file(f.filename) for f in files_to_check):
            flash('Only .csv files are supported.', 'error')
            return redirect(url_for('index'))

        # Save uploaded files
        online_path = None
        offline_path = None

        if online_file:
            online_name = secure_filename(online_file.filename or 'online.csv')
            online_path = os.path.join(app.config['UPLOAD_FOLDER'], online_name)
            online_file.save(online_path)

        if offline_file:
            offline_name = secure_filename(offline_file.filename or 'offline.csv')
            offline_path = os.path.join(app.config['UPLOAD_FOLDER'], offline_name)
            offline_file.save(offline_path)

        # Save report file if provided
        report_path = None
        if report_file:
            report_name = secure_filename(report_file.filename or 'report.csv')
            report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_name)
            report_file.save(report_path)

        try:
            # Process CSV files (only if they were uploaded)
            online_series = None
            offline_series = None

            if online_path:
                online_series = process_online_csv(online_path, view_type, operating_start_hour)
            else:
                # Create empty series if no online file
                if view_type == 'daily':
                    online_series = pd.Series(dtype=float)
                else:
                    online_series = pd.Series(0.0, index=range(24))
                print("No online CSV uploaded - using zero values")

            if offline_path:
                offline_series = process_offline_csv(offline_path, view_type, operating_start_hour)
            else:
                # Create empty series if no offline file
                if view_type == 'daily':
                    offline_series = pd.Series(dtype=float)
                else:
                    offline_series = pd.Series(0.0, index=range(24))
                print("No offline CSV uploaded - using zero values")

            # Process report file if provided
            report_series = None
            if report_path:
                report_series = process_report_csv(report_path, view_type, operating_start_hour)

            # Create combined dataframe based on view type
            if view_type == 'daily':
                # For daily view, we need to align dates from all series
                all_dates = set()
                if len(online_series) > 0:
                    all_dates.update(online_series.index)
                if len(offline_series) > 0:
                    all_dates.update(offline_series.index)
                if report_series is not None and len(report_series) > 0:
                    all_dates.update(report_series.index)

                # Convert to sorted list
                all_dates = sorted(list(all_dates))

                # Create aligned series
                online_aligned = pd.Series(0.0, index=all_dates)
                offline_aligned = pd.Series(0.0, index=all_dates)

                if len(online_series) > 0:
                    online_aligned.update(online_series)
                if len(offline_series) > 0:
                    offline_aligned.update(offline_series)

                df = pd.DataFrame({
                    'Online': online_aligned,
                    'Offline': offline_aligned,
                })
                df['Total'] = df['Online'] + df['Offline']

                # Add report data if available
                if report_series is not None:
                    report_aligned = pd.Series(0.0, index=all_dates)
                    if len(report_series) > 0:
                        report_aligned.update(report_series)
                    df['Report'] = report_aligned
            else:
                # For hourly view (existing logic)
                df = pd.DataFrame({
                    'Online': online_series,
                    'Offline': offline_series,
                })
                df['Total'] = df['Online'] + df['Offline']

                # Add report data if available
                if report_series is not None:
                    df['Report'] = report_series

            # Generate display data based on view type
            rows = []

            if view_type == 'daily':
                # Daily view - iterate through dates
                target_dates = []
                if report_series is not None:
                    # Find dates that have non-zero report data
                    target_dates = [d for d in df.index if report_series is not None and d in report_series.index and report_series[d] > 0]
                    print(f"Report dates detected: {target_dates}")

                for date_idx in df.index:
                    row_data = {
                        'label': date_idx.strftime('%d %b %Y'),  # Format: "22 Aug 2025"
                        'online': float(df.loc[date_idx, 'Online']),
                        'offline': float(df.loc[date_idx, 'Offline']),
                        'total': float(df.loc[date_idx, 'Total']),
                        'show_in_report': date_idx in target_dates,
                        'has_discrepancy': False,
                        'report': 0.0,
                        'difference': 0.0
                    }

                    # Add report data and check for discrepancies if report is available
                    if report_series is not None and 'Report' in df.columns:
                        row_data['report'] = float(df.loc[date_idx, 'Report'])

                        # Calculate difference (Total - Report) for dates that have report data
                        if date_idx in target_dates:
                            total_val = row_data['total']
                            report_val = row_data['report']
                            row_data['difference'] = total_val - report_val

                            # Consider discrepancy if difference is more than 0.01
                            if abs(row_data['difference']) > 0.01:
                                row_data['has_discrepancy'] = True

                    rows.append(row_data)
            else:
                # Hourly view (existing logic)
                target_hours = []
                if report_series is not None:
                    # Find hours that have non-zero report data
                    target_hours = [h for h in range(24) if report_series[h] > 0]
                    print(f"Report hours detected: {target_hours}")

                for h in range(24):
                    row_data = {
                        'label': format_hour_label(h),
                        'online': float(df.loc[h, 'Online']),
                        'offline': float(df.loc[h, 'Offline']),
                        'total': float(df.loc[h, 'Total']),
                        'show_in_report': h in target_hours,
                        'has_discrepancy': False,
                        'report': 0.0,
                        'difference': 0.0
                    }

                    # Add report data and check for discrepancies if report is available
                    if report_series is not None:
                        row_data['report'] = float(df.loc[h, 'Report'])

                        # Calculate difference (Total - Report) for hours that have report data
                        if h in target_hours:
                            total_val = row_data['total']
                            report_val = row_data['report']
                            row_data['difference'] = total_val - report_val

                            # Consider discrepancy if difference is more than 0.01
                            if abs(row_data['difference']) > 0.01:
                                row_data['has_discrepancy'] = True

                    rows.append(row_data)

            # Calculate totals
            footer = {
                'online_sum': float(df['Online'].sum()),
                'offline_sum': float(df['Offline'].sum()),
                'total_sum': float(df['Total'].sum()),
                'has_report': report_series is not None,
                'has_online': online_path is not None,
                'has_offline': offline_path is not None,
                'view_type': view_type
            }

            if report_series is not None and 'Report' in df.columns:
                footer['report_sum'] = float(df['Report'].sum())
                footer['difference_sum'] = footer['total_sum'] - footer['report_sum']

            # Clean up uploaded files
            try:
                if online_path:
                    os.remove(online_path)
                if offline_path:
                    os.remove(offline_path)
                if report_path:
                    os.remove(report_path)
            except:
                pass

            return render_template('index.html', rows=rows, footer=footer, has_result=True, view_type=view_type)

        except Exception as e:
            flash(f'Error processing CSV files: {str(e)}', 'error')
            return redirect(url_for('index'))

    # GET request
    return render_template('index.html', rows=[], footer=None, has_result=False, view_type='hourly')

if __name__ == '__main__':
    # For production deployment, use gunicorn; for local debugging use the line below
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)