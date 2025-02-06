import pandas as pd
import plotly.express as px
import os
from django.shortcuts import render
from django.conf import settings
import datetime
import dash_leaflet as dl
import json
from django.http import HttpResponse,JsonResponse
from io import StringIO
import csv
import plotly.express as px
import plotly.io as pio


def load_and_process_data(start_date=None, end_date=None):
    # Load raw data
    appointment = pd.read_csv(
        r'C:\Users\Admin\Desktop\zip_codes\zip\data\appointment_list.csv',
        low_memory=False
    )

    # Deduplicate based on 'appointment_id'
    appointment = appointment.drop_duplicates(subset=['appointment_id'])

    # Convert date and numeric columns
    appointment['appointment_date'] = pd.to_datetime(appointment['cdate'], format='%d-%m-%Y %H:%M', errors='coerce')
    appointment['user_id'] = appointment['user_id'].astype(str)
    appointment['g_id'] = appointment['g_id'].astype(str)
    appointment.fillna(0, inplace=True)

    # Load additional datasets
    user = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\user.csv', low_memory=False)
    user['email'] = user.get('email', 'No Email')  # Ensure 'email' column exists
    user['user_id'] = user['user_id'].astype(str)
    user = user[['user_id', 'email']]

    address = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\address.csv', low_memory=False)
    address['user_id'] = address['user_id'].astype(str)
    address = address[['user_id', 'state']]

    # Merge appointment data with user and address
    appointment = pd.merge(appointment, address, on='user_id', how='left')
    appointment = pd.merge(appointment, user, on='user_id', how='left')
    appointment['state'] = appointment['state'].fillna('Unknown')
    appointment['email'] = appointment['email'].fillna('No Email')

    # User classification logic
    today = datetime.datetime.now()
    user_last_appointment = appointment.groupby('user_id')['appointment_date'].max().reset_index()
    user_last_appointment['days_since_last_appointment'] = (today - user_last_appointment['appointment_date']).dt.days

    # Calculate default start and end dates from the data
    data_start_date = appointment['appointment_date'].min()
    data_end_date = appointment['appointment_date'].max()

    print("Data range in the dataset:")
    print(f"Start date: {data_start_date}")
    print(f"End date: {data_end_date}")

    # Apply date filtering if necessary
    if start_date:
        appointment = appointment[appointment['appointment_date'] >= pd.to_datetime(start_date)]
    if end_date:
        appointment = appointment[appointment['appointment_date'] <= pd.to_datetime(end_date)]

    return appointment,user_last_appointment,user, data_start_date, data_end_date


def home(request):
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    appointment,user_last_appointment,user, data_start_date, data_end_date = load_and_process_data()
    
    STATUS_MAPPING = {
        'N': 'Not Assigned',
        'D': 'Assigned',
        'O': 'On-the-Way',
        'W': 'In-Progress',
        'C': 'Cancelled',
        'S': 'Completed',
        'F': 'Failure',
        'R': 'Rejected',
        'L': 'Rescheduled',
        'P': 'Paid'
    }

    # Deduplication for total revenue (if necessary)
    appointment_deduplicated = appointment.drop_duplicates(subset=['user_id'])

    # Merge classification back to user data
    user_data = pd.merge(user_last_appointment, user, on='user_id', how='left')

    # Load and prepare address data (address_mapped)
    address_mapped = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\address_mapped.csv', low_memory=False)
    address_mapped['user_id'] = address_mapped['user_id'].astype(str)
    appointment = pd.merge(appointment, address_mapped[['user_id', 'state']], on='user_id', how='left')

    # Rename the 'state_y' column to 'state' and drop the 'state_x' column
    appointment['state'] = appointment['state_y']
    appointment.drop(columns=['state_x', 'state_y'], inplace=True)

    # ----------------- State-wise Revenue Chart -----------------
    state_revenue = appointment.groupby('state')['total_final'].sum().reset_index()

    # Deduplicate state revenue
    state_revenue_deduplicated = state_revenue.drop_duplicates(subset=['state'])

    # Create the state revenue chart
    state_revenue_chart = px.bar(
        state_revenue_deduplicated, 
        x='state', 
        y='total_final', 
        title='State-wise Revenue'
    )    
    
    # ----------------- Complaints Chart -----------------
    complaints_data = appointment[appointment['if_complain'] == 'Yes']  

    complaints_by_gid = complaints_data.groupby('g_id').size().reset_index(name='Complaint Count')  # Group by g_id and count the complaints
    if complaints_data.empty:
        complaints_data = pd.DataFrame({'g_id': [], 'Complaint Count': []})
    complaints_chart = px.bar(
        complaints_by_gid, 
        x='g_id', 
        y='Complaint Count', 
        title='Complaints by G_ID'
    )

    # Appointment Summary Chart
    appointment_summary = appointment['status'].map(STATUS_MAPPING).value_counts().reset_index()
    appointment_summary.columns = ['Status', 'Count']
    appointment_summary_chart = px.bar(
        appointment_summary, 
        x='Status', 
        y='Count', 
        title='Appointment Summary by Status'
    )
    
    # Heatmap
    users = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\user.csv', low_memory=False)
    appointments = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\appointment_list.csv', low_memory=False)
    users['user_id'] = users['user_id'].astype(str)
    appointments['user_id'] = appointments['user_id'].astype(str)
    merged_data = pd.merge(appointments, users[['user_id', 'zip']], on='user_id', how='left')
    heatmap_data = merged_data.groupby(['zip', 'g_id']).size().reset_index(name='Count')
    heatmap = px.density_heatmap(
        heatmap_data, x='zip', y='g_id', z='Count',
        title="Heatmap: G_IDs Close to Users by Zip Code",
        color_continuous_scale="Viridis"
    )


    state_names = {
        "AL": "Alabama",
        "AR": "Arkansas",
        "AZ": "Arizona",
        "NY": "New York",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut",
        "DC": "District of Columbia",
        "DE": "Delaware",
        "FL": "Florida",
        "GA": "Georgia",
        "HI": "Hawaii",
        "IL": "Illinois",
        "IN": "Indiana",
        "KY": "Kentucky",
        "LA": "Louisiana",
        "MA": "Massachusetts",
        "MD": "Maryland",
        "ME": "Maine",
        "MI": "Michigan",
        "MN": "Minnesota",
        "MO": "Missouri",
        "MS": "Mississippi",
        "MT": "Montana",
        "NC": "North Carolina",
        "NE": "Nebraska",
        "NJ": "New Jersey",
        "NH": "New Hampshire",
        "NV": "Nevada",
        "OH": "Ohio",
        "OK": "Oklahoma",
        "PA": "Pennsylvania",
        "SC": "South Carolina",
        "TX": "Texas",
        "TN": "Tennessee",
        "UT": "Utah",
        "VA": "Virginia",
        "WA": "Washington",
        "WY": "Wyoming",
    }
    new_filtered_data = pd.merge(appointment, address_mapped[['user_id', 'zip']], on='user_id', how='left')

    # Coordinate Extraction
    zip_coordinates = (
        address_mapped.groupby('zip')[['latitude', 'longitude']]
        .mean()
        .dropna()
        .reset_index()
        .set_index('zip')
        .to_dict('index')
    )
    zip_coordinates = {
        zip_code: (coords['latitude'], coords['longitude'])
        for zip_code, coords in zip_coordinates.items()
    }

    # Marker Preparation
    merged_data = new_filtered_data
    zip_user_data = merged_data.groupby('zip').agg({
        'user_id': lambda x: sorted(set(x))  # Remove duplicates and sort
    }).reset_index()

    markers = []
    for zip_code, user_ids in zip(zip_user_data['zip'], zip_user_data['user_id']):
        if zip_code in zip_coordinates:
            user_id_count = len(user_ids)  # Unique user count

            state_abbr = address_mapped[address_mapped['zip'] == zip_code]['state'].iloc[0]
            state_name = state_names.get(state_abbr, 'Unknown State')

            markers.append({
                "latitude": float(zip_coordinates[zip_code][0]),
                "longitude": float(zip_coordinates[zip_code][1]),
                "zip": str(zip_code),
                "state": state_name,
                "user_count": user_id_count,
                "user_ids": [str(uid) for uid in user_ids[:5]]  # Convert to strings
            })

    print(zip_user_data.head())  # Debugging

    # KPI Calculations and context preparation
    total_appointments = appointment['appointment_id'].nunique()
    total_users = appointment['user_id'].nunique()
    total_revenue = appointment['total_final'].sum()
    avg_days_to_appointment = (pd.to_datetime(appointment['appointment_date'].max()) - pd.to_datetime(appointment['appointment_date'].min())).days

    context = {
        'total_appointments': total_appointments,
        'total_users': total_users,
        'total_revenue': f"{total_revenue:.2f}",
        'avg_days_to_appointment': avg_days_to_appointment,
        'appointment_summary_chart': appointment_summary_chart.to_json(),

        'state_revenue_chart': state_revenue_chart.to_json(),
        'complaints_chart': complaints_chart.to_json(),
        'heatmap': heatmap.to_json(),
        'markers': json.dumps(markers)       
    }

    return render(request, 'home_page.html', context)


def user_status_analysis(request):
    # Load raw data
    appointment = pd.read_csv(
        r'C:\Users\Admin\Desktop\zip_codes\zip\data\appointment_list.csv',
        low_memory=False
    )

    # Deduplicate based on 'appointment_id'
    appointment = appointment.drop_duplicates(subset=['appointment_id'])
    # Convert date and numeric columns
    appointment['appointment_date'] = pd.to_datetime(appointment['cdate'], format='%d-%m-%Y %H:%M', errors='coerce')
    appointment['user_id'] = appointment['user_id'].astype(str)
    appointment['g_id'] = appointment['g_id'].astype(str)
    appointment.fillna(0, inplace=True)
    # Load additional datasets
    user = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\user.csv', low_memory=False)
    user['email'] = user.get('email', 'No Email')  # Ensure 'email' column exists
    user['user_id'] = user['user_id'].astype(str)
    user = user[['user_id', 'email']]
    
    user_visit_logs = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\user_address_mapping.csv', low_memory=False)
    user_visit_logs['user_id'] = user_visit_logs['user_id'].astype(str)
    user_visit_logs = user_visit_logs[['user_id', 'state', 'county']]
    
    # Merge appointment data with user and address
    appointment = pd.merge(appointment, user_visit_logs, on='user_id', how='left')
    appointment = pd.merge(appointment, user, on='user_id', how='left')
    appointment['state'] = appointment['state'].fillna('Unknown')
    appointment['email'] = appointment['email'].fillna('No Email')

    # User classification logic
    today = datetime.datetime.now()
    user_last_appointment = appointment.groupby('user_id')['appointment_date'].max().reset_index()
    user_last_appointment['days_since_last_appointment'] = (today - user_last_appointment['appointment_date']).dt.days
    def classify_user(days):
        if pd.isna(days):
            return 'No Appointments'
        elif days < 90:
            return 'Potential'
        elif days < 180:
            return 'Inactive (6 Months)'
        elif days <= 360:
            return 'Recurring'
        else:
            return 'Lost'

    user_last_appointment['status'] = user_last_appointment['days_since_last_appointment'].apply(classify_user)
    user_data = pd.merge(user_last_appointment, user, on='user_id', how='left')

    # Filter Lost Users
    lost_users = user_data[user_data['status'] == 'Lost']

    # Remove duplicate user_id entries from user_visit_logs before merging
    user_visit_logs_unique = user_visit_logs[['user_id', 'county']].drop_duplicates()

    # Merge lost users with county data
    lost_users_with_county = pd.merge(lost_users, user_visit_logs_unique, on='user_id', how='left')


    # Count unique lost users per county
    lost_users_count_per_county = lost_users_with_county.drop_duplicates(subset=['user_id', 'county'])
    lost_users_count_per_county = lost_users_count_per_county['county'].value_counts().reset_index()
    lost_users_count_per_county.columns = ['county', 'lost_user_count']


    # Handle chart data and filter logic on POST request
    if request.method == "POST":
        # Get the filters from the POST request body
        import json
        data = json.loads(request.body)
        county = data.get("county")
        user_status = data.get("user_status", "All")

        filtered_users = user_data.copy()

        if county:
            state_user_ids = appointment[appointment['county'] == county]['user_id']
            filtered_users = filtered_users[filtered_users['user_id'].isin(state_user_ids)]

        if user_status != "All":
            filtered_users = filtered_users[filtered_users['status'] == user_status]

        # Count the statuses
        status_counts = filtered_users['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']

        # Return the data as JSON to update the chart
        return JsonResponse({"chartData": status_counts.to_dict(orient='records'),
                             "lostUsersCountyData": lost_users_count_per_county.to_dict(orient='records')})

    # Render the page with state options for the filter
    countys = appointment['county'].unique()
    if request.GET.get('export') == 'true':
        county = request.GET.get("county", None)
        user_status = request.GET.get("user_status", "All")

        filtered_appointments = appointment.copy()

        if county:
            filtered_appointments = filtered_appointments[filtered_appointments['county'] == county]

        if user_status != "All":
            user_ids = user_data[user_data['status'] == user_status]['user_id']
            filtered_appointments = filtered_appointments[filtered_appointments['user_id'].isin(user_ids)]

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="user_data.csv"'

        writer = csv.writer(response)
        writer.writerow(['User ID', 'County', 'Status', 'Appointment Count'])

        for user_id, group in filtered_appointments.groupby('user_id'):
            writer.writerow([user_id,
                             group['county'].iloc[0],
                             group['status'].iloc[0],
                             len(group)])

        return response

    appointment['if_complain'] = appointment['if_complain'].astype(str)
    # Aggregate appointment counts by G_ID and if_complain status
    g_id_summary = (
        appointment.groupby(['g_id', 'if_complain'])
        .agg(appointment_count=('appointment_id', 'count'))
        .reset_index()
    )

    # Create a bar chart
    g_id_fig = px.bar(
        g_id_summary,
        x='g_id',
        y='appointment_count',
        color='if_complain',  # Differentiate bars based on complaint status
        barmode='group',  # Group bars for better comparison
        title="G_ID Counts vs. Appointment (Based on Complaints)",
        labels={'g_id': 'G_ID', 'appointment_count': 'Appointment Count', 'if_complain': 'Complaint Status'},
        color_discrete_map={'0': '#636EFA', '1': '#EF553B'}  # Example colors for No Complaint (0) & Complaint (1)
    )

    # Convert to HTML
    g_id_html = pio.to_html(g_id_fig, full_html=False)

    return render(request, 'user_status_analysis.html', {
        "countys": countys,
        "lostUsersCountyData": lost_users_count_per_county,"g_id_html":g_id_html
    })

def total_final_summmary(request):
    # Load the appointment data without filtering by date
    appointment, user_last_appointment, user, data_start_date, data_end_date = load_and_process_data()

    # Calculate start and end dates from the data
    start_date = data_start_date
    end_date = data_end_date

    # Calculate summary data
    g_id_summary = appointment.groupby(['g_id', 'state']).agg(
        Revenue=('total_final', 'sum'),
        Appointment_Count=('appointment_id', 'size')
    ).reset_index()

    # G_ID Complaints
    appointment['if_complain'] = appointment['if_complain'].map({'Yes': 1, 'No': 0})
    complaints_data = appointment[appointment['if_complain'] == 1]
    g_id_complaints = complaints_data.groupby(['g_id', 'state']).size().reset_index(name='Complaints')

    # User State Count
    user_state_count = appointment.groupby('state')['user_id'].nunique().reset_index()
    user_state_count.columns = ['State', 'User_Count']

    # Pass data to template
    context = {
        'g_id_summary': g_id_summary.to_dict(orient='records'),
        'g_id_complaints': g_id_complaints.to_dict(orient='records'),
        'user_state_count': user_state_count.to_dict(orient='records'),
        'start_date': start_date.date() if pd.notna(start_date) else None,
        'end_date': end_date.date() if pd.notna(end_date) else None,
    }

    return render(request, 'total_final_summmary.html', context)


def export_g_id_summary(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    appointment, user_last_appointment, user, data_start_date, data_end_date = load_and_process_data(start_date, end_date)

    g_id_summary = appointment.groupby(['g_id', 'state']).agg(
        Revenue=('total_final', 'sum'),
        Appointment_Count=('appointment_id', 'size')
    ).reset_index()

    output = StringIO()
    g_id_summary.to_csv(output, index=False)
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="g_id_summary.csv"'
    return response


def export_g_id_complaints(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    appointment, user_last_appointment, user, data_start_date, data_end_date = load_and_process_data(start_date, end_date)

    appointment['if_complain'] = appointment['if_complain'].str.strip().str.lower().map({'yes': 1, 'no': 0}).fillna(0)
    complaints_data = appointment[appointment['if_complain'] == 1]
    g_id_complaints = complaints_data.groupby(['g_id', 'state']).size().reset_index(name='Complaints')

    output = StringIO()
    g_id_complaints.to_csv(output, index=False)
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="g_id_complaints.csv"'
    return response


def export_user_state_count(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    appointment, user_last_appointment, user, data_start_date, data_end_date = load_and_process_data(start_date, end_date)

    user_state_count = appointment.groupby('state')['user_id'].nunique().reset_index()
    user_state_count.columns = ['State', 'User Count']

    output = StringIO()
    user_state_count.to_csv(output, index=False)
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_state_count.csv"'
    return response


def appointment_analysis(request):
    appointment, user_last_appointment, user, data_start_date, data_end_date = load_and_process_data()

    start_date = request.GET.get('start_date', data_start_date.date())
    end_date = request.GET.get('end_date', data_end_date.date())
    
    # Filter appointments based on selected date range
    filtered_data = appointment[
        (appointment['appointment_date'] >= pd.to_datetime(start_date)) &
        (appointment['appointment_date'] <= pd.to_datetime(end_date))
    ]

    # Histogram: Distribution of appointments over time
    histogram_fig = px.histogram(
        filtered_data,
        x='appointment_date',
        nbins=30,
        title="Days to Appointment Distribution",
        labels={'appointment_date': 'Appointment Date'}
    )
    histogram_html = pio.to_html(histogram_fig, full_html=False)

    # Line Chart: Appointment trends over time
    avg_days_summary = (
        filtered_data.groupby('appointment_date')
        .size()
        .reset_index(name='count')
    )

    line_fig = px.line(
        avg_days_summary,
        x='appointment_date',
        y='count',
        title="Appointment Trends Over Time",
        labels={'appointment_date': 'Appointment Date', 'count': 'Number of Appointments'}
    )
    line_chart_html = pio.to_html(line_fig, full_html=False)

    # Render HTML template with the graphs
    context = {
        'histogram_html': histogram_html,
        'line_chart_html': line_chart_html,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request,'appointment_analysis.html',context)
    
def registration_analysis(request):
    appointment, user_last_appointment, user, data_start_date, data_end_date = load_and_process_data()

    
    # Add additional fields for analysis
    user = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\user.csv', low_memory=False)
    
    # Ensure 'user_id' is of the same type in both DataFrames (e.g., int64)
    user['user_id'] = user['user_id'].astype(int)  # or .astype(str) depending on your data
    appointment['user_id'] = appointment['user_id'].astype(int)  # Ensure consistency
    
    user['registered_date'] = pd.to_datetime(appointment['cdate'], format='%d-%m-%Y %H:%M', dayfirst=True)
    
    # Merge appointment with user on 'user_id'
    appointment = appointment.merge(user[['user_id', 'registered_date']], on='user_id', how='left')
    
    appointment['days_to_appointment'] = (appointment['appointment_date'] - appointment['registered_date']).dt.days
    appointment = appointment[appointment['days_to_appointment'].notnull() & (appointment['days_to_appointment'] >= 0)]
    appointment['appointment_index'] = appointment.groupby('user_id').cumcount() + 1
    appointment = appointment.sort_values(by=['user_id', 'appointment_date'])
    appointment['days_between_appointments'] = appointment.groupby('user_id')['appointment_date'].diff().dt.days
    
    appointment_gap_summary = (
        appointment
        .groupby('appointment_index')
        .agg(
            avg_days_between_appointments=('days_between_appointments', 'mean'),
            appointment_count=('appointment_id', 'count')
        )
        .reset_index()
    )
    selected_quarter = request.GET.get('quarter', None)

    # Filter data by quarter
    if selected_quarter:
        filtered_data = appointment[appointment['registered_date'].dt.to_period('Q') == selected_quarter]
    else:
        filtered_data = appointment

    # Histogram: Distribution of Days Between Registration and Appointment
    histogram_fig = px.histogram(
        filtered_data,
        x='days_to_appointment',
        nbins=30,
        title="Distribution of Days Between Registration and Appointment",
        color_discrete_sequence=['#636EFA']
    )
    histogram_html = pio.to_html(histogram_fig, full_html=False)

    # Line Chart: Average Days to Appointment Over Time
    avg_days_summary = (
        filtered_data
        .groupby(filtered_data['registered_date'].dt.to_period('M'))
        .agg(avg_days_to_appointment=('days_to_appointment', 'mean'))
        .reset_index()
    )
    avg_days_fig = px.line(
        avg_days_summary,
        x=avg_days_summary['registered_date'].dt.to_timestamp(),
        y='avg_days_to_appointment',
        title="Average Days to Appointment Over Time",
        markers=True
    )
    avg_days_html = pio.to_html(avg_days_fig, full_html=False)

    # Line Chart: Gaps Between Consecutive Appointments
    gap_fig = px.line(
        appointment_gap_summary,
        x='appointment_index',
        y='avg_days_between_appointments',
        title='Average Days Between Consecutive Appointments',
        markers=True
    )
    gap_html = pio.to_html(gap_fig, full_html=False)

    # Display Metrics
    avg_gap = filtered_data['days_to_appointment'].mean()
    total_appointments = filtered_data['appointment_id'].nunique()
    total_customers = filtered_data['user_id'].nunique()

    metrics = {
        'avg_gap': round(avg_gap, 2),
        'total_appointments': total_appointments,
        'total_customers': total_customers
    }
    users_with_appointments = set(appointment['user_id'].unique())
    all_users = set(user['user_id'].unique())
    users_without_appointments = all_users - users_with_appointments

    # Create a DataFrame
    no_booking_df = pd.DataFrame({'user_id': list(users_without_appointments)})
    no_booking_df['count'] = 1  # Each user counts as 1

    # Aggregate by registration year
    no_booking_summary = (
        user[user['user_id'].isin(no_booking_df['user_id'])]
        .groupby(user['registered_date'].dt.year)
        .agg(no_booking_count=('user_id', 'count'))
        .reset_index()
    )

    # Create a bar chart with year on x-axis
    no_booking_fig = px.bar(
        no_booking_summary,
        x='registered_date',  # Now this represents only the year
        y='no_booking_count',
        title="Users Registered but No Booking (by Year)",
        labels={'registered_date': 'Year', 'no_booking_count': 'Users Without Booking'},
        color_discrete_sequence=['#EF553B']
    )

    # Convert to HTML
    no_booking_html = pio.to_html(no_booking_fig, full_html=False)

    # Render HTML template with graphs and metrics
    context = {
        'histogram_html': histogram_html,
        'avg_days_html': avg_days_html,
        'gap_html': gap_html,
        'no_booking_html':no_booking_html,
        'metrics': metrics,
        'quarters': appointment['registered_date'].dt.to_period('Q').unique(),
        'selected_quarter': selected_quarter
    }
    return render(request, 'registration_analysis.html',context)

def groomer_analysis(request):
    # Load g.csv
    g_df = pd.read_csv(
        r'C:\Users\Admin\Desktop\zip_codes\zip\data\g.csv',
        low_memory=False
    )  # Replace with the actual path to your CSV file
    print(g_df.columns)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    city_filter = request.GET.get('city')  # Get selected city from the request

    # Convert date columns to datetime format if needed
    if 'cdate' in g_df.columns:
        g_df['cdate'] = pd.to_datetime(g_df['cdate'], errors='coerce')

    # If filtering by date is required
    if start_date and end_date:
        g_df = g_df[
            (g_df['cdate'] >= pd.to_datetime(start_date)) &
            (g_df['cdate'] <= pd.to_datetime(end_date))
        ]

    # If filtering by city is required
    if city_filter:
        g_df = g_df[g_df['city'] == city_filter]

    # Group by city and count users
    location_summary = g_df.groupby('city').size().reset_index(name='count')

    # Create bar chart for User vs. Location
    location_fig = px.bar(
        location_summary,
        x='city',
        y='count',
        title="User vs. Location",
        labels={'city': 'City', 'count': 'Number of Users'},
        color='count',
        color_continuous_scale='Viridis'  # You can change the color scale here
    )

    # Adjust chart layout for better visibility
    location_fig.update_layout(
        xaxis_tickangle=45,  # Rotate x-axis labels to avoid overlap
        margin={'l': 50, 'r': 50, 't': 50, 'b': 150},  # Adjust margins to make space
        height=600,  # Specify chart height
        width=1000  # Specify chart width
    )

    # Convert plotly figure to HTML for rendering
    location_chart_html = pio.to_html(location_fig, full_html=False)

    # Get list of cities for the filter dropdown
    city_options = g_df['city'].unique()

    # Render template
    context = {
        'location_chart_html': location_chart_html,
        'start_date': start_date,
        'end_date': end_date,
        'city_options': city_options,  # Pass cities to the template for the dropdown
        'selected_city': city_filter,  # Pass selected city
    }
    return render(request, 'groomer_analysis.html', context)
