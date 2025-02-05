import pandas as pd

# Load CSV files into pandas DataFrames
address_df = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\address_mapped.csv')
user_visits_df = pd.read_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\user_visit_logs.csv')

# Merge user_visit_logs.csv with address_mapped.csv on 'user_id'
merged_df = user_visits_df.merge(address_df, on='user_id', how='left')

# Select only the required columns
result_df = merged_df[['ip_address','user_visit_id','user_id', 'county', 'state', 'zip', 'status', 'latitude', 'longitude']]

# Save the result to a new CSV file
result_df.to_csv(r'C:\Users\Admin\Desktop\zip_codes\zip\data\user_address_mapping.csv', index=False)

# Print the result
print(result_df)