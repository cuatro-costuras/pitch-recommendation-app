import pandas as pd
import streamlit as st
import os

# Dictionary to map pitch acronyms to full names
pitch_type_mapping = {
    "FF": "Four-Seam Fastball",
    "SL": "Slider",
    "CU": "Curveball",
    "CH": "Changeup",
    "FS": "Splitter",
    "SI": "Sinker",
    "FC": "Cutter",
    "KC": "Knuckle Curve",
    "KN": "Knuckleball",
    "SV": "Sweeper",
    "ST": "Sweeping Curve",
    "CS": "Slow Curve",
}

# Function to load and concatenate all available files
@st.cache_data
def load_all_data():
    # Base path for the files
    base_path = './'  # Adjust if files are in a subdirectory

    # Initialize an empty DataFrame
    combined_data = pd.DataFrame()

    # Loop through all files matching the naming pattern
    for year in [2022, 2023]:  # Adjust for actual years available
        for month in range(1, 13):  # Months 1 to 12
            file_name = f'statcast_{year}_{month:02d}.csv.gz'
            file_path = os.path.join(base_path, file_name)

            try:
                # Load the monthly file
                data = pd.read_csv(file_path, compression='gzip')

                # Map pitch types to full names
                data['pitch_type'] = data['pitch_type'].map(pitch_type_mapping).fillna('Unknown')
                data = data[data['pitch_type'] != 'Unknown']  # Remove unmapped pitch types

                # Append to the combined DataFrame
                combined_data = pd.concat([combined_data, data], ignore_index=True)

            except FileNotFoundError:
                st.warning(f"File not found: {file_name}")
            except Exception as e:
                st.error(f"Error loading file {file_name}: {e}")

    return combined_data

# Load all data
data = load_all_data()

# Ensure data is loaded before continuing
if data.empty:
    st.error("No data available. Please ensure the data files are in the correct directory.")
else:
    # Define success criteria
    data['success'] = (
        (data['events'] == 'strikeout') |
        (data['description'] == 'swinging_strike') |
        (data['description'] == 'foul') |
        (data['description'] == 'called_strike') |
        ((data['launch_speed'] < 80) & (data['launch_speed'].notna()))
    )

    # Add a column for the previous pitch type
    data['prev_pitch_type'] = data['pitch_type'].shift(1)

    # Streamlit App
    st.title("Pitch Sequence Success Rates")

    # Add the descriptive message
    st.write(
        "Have you ever been in the middle of an at-bat and wondered what pitch to throw next? "
        "Use our tool to find what pitches are most successful after the pitch you just threw."
    )

    st.write("**Disclaimer:** This tool uses all available Statcast data from 2022 through 2024.")

    # Dropdowns for filters
    prev_pitch_type = st.selectbox(
        "Select Previous Pitch Type",
        options=data['prev_pitch_type'].dropna().unique(),
        index=0
    )

    pitcher_hand = st.selectbox(
        "Select Pitcher Handedness",
        options=data['p_throws'].dropna().unique(),
        index=0
    )

    hitter_hand = st.selectbox(
        "Select Hitter Handedness",
        options=data['stand'].dropna().unique(),
        index=0
    )

    # Filter data based on selections
    filtered_data = data[
        (data['prev_pitch_type'] == prev_pitch_type) &
        (data['p_throws'] == pitcher_hand) &
        (data['stand'] == hitter_hand)
    ]

    # Group by pitch type and calculate success rate
    pitch_success = filtered_data.groupby('pitch_type')['success'].agg(['mean', 'count']).reset_index()
    pitch_success.columns = ['Pitch Type', 'Success Rate', 'Occurrences']

    # Calculate prior success rate
    prior_success_rate = data['success'].mean()

    # Add Weighted Success Rate
    m = 10  # Minimum sample size for prior weighting
    pitch_success['Weighted Success Rate'] = (
        (pitch_success['Occurrences'] * pitch_success['Success Rate'] + m * prior_success_rate) /
        (pitch_success['Occurrences'] + m)
    )

    # Sort by Weighted Success Rate and keep only the top 5 rows
    pitch_success = pitch_success.sort_values(by='Weighted Success Rate', ascending=False).head(5).reset_index(drop=True)
    pitch_success['Rank'] = pitch_success.index + 1

    # Display the table
    st.write("### Top 5 Ranked Pitch Recommendations")
    st.table(pitch_success[['Rank', 'Pitch Type', 'Success Rate', 'Weighted Success Rate', 'Occurrences']])

    # Add a key below the table
    st.write("### Key")
    st.write(
        """
        - **Success Rate**: The percentage of times a pitch sequence resulted in a successful outcome 
          (e.g., strikeouts, swinging strikes, foul balls, called strikes, or balls hit under 80 mph exit velocity).
        - **Weighted Success Rate**: Adjusted success rate accounting for small sample sizes by factoring in 
          the global average success rate and a minimum sample size threshold.
        - **Occurrences**: The number of times the selected pitch sequence occurred.
        """
    )
