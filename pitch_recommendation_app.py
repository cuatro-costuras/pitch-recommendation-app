import pandas as pd
import streamlit as st

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

# Function to load and filter the dataset
@st.cache_data
def load_filtered_data(file_path, year_filter=2021):
    chunks = pd.read_csv(file_path, chunksize=500000)

    filtered_chunks = []
    for chunk in chunks:
        # Print available columns for debugging
        print(f"Chunk columns: {chunk.columns.tolist()}")

        if 'year' in chunk.columns:  # Ensure the 'year' column exists
            filtered_chunk = chunk[chunk['year'] >= year_filter]  # Filter by year
            print(f"Filtered chunk rows: {filtered_chunk.shape[0]}")  # Debugging info
            if not filtered_chunk.empty:
                filtered_chunks.append(filtered_chunk)

    # Concatenate all filtered chunks or return an empty DataFrame if no data matches
    if filtered_chunks:
        filtered_data = pd.concat(filtered_chunks, ignore_index=True)
    else:
        print("No data matched the filtering criteria.")
        filtered_data = pd.DataFrame(columns=['pitch_type', 'p_throws', 'stand', 'events', 'description', 'launch_speed', 'year'])

    # Map pitch types to full names
    if 'pitch_type' in filtered_data.columns:
        filtered_data['pitch_type'] = filtered_data['pitch_type'].map(pitch_type_mapping).fillna('Unknown')
        filtered_data = filtered_data[filtered_data['pitch_type'] != 'Unknown']  # Remove unmapped rows
    else:
        print("Warning: 'pitch_type' column is missing in the data.")

    return filtered_data

# Load the filtered dataset (only data from 2021 and later)
data = load_filtered_data('smaller_statcast.csv', year_filter=2021)

# Define success criteria
data['success'] = (
    (data['events'] == 'strikeout') |                     # Strikeouts
    (data['description'] == 'swinging_strike') |          # Swinging strikes
    (data['description'] == 'foul') |                    # Foul balls
    (data['description'] == 'called_strike') |           # Called strikes
    ((data['launch_speed'] < 80) & (data['launch_speed'].notna()))  # Weak contact (< 80 mph)
)

# Add a column for the previous pitch type
if 'pitch_type' in data.columns:
    data['prev_pitch_type'] = data['pitch_type'].shift(1)
else:
    data['prev_pitch_type'] = None  # Handle missing column gracefully

# Streamlit App
st.title("Pitch Sequence Success Rates")

# Add the descriptive message
st.write(
    "Have you ever been in the middle of an at-bat and wondered what pitch to throw next? "
    "Use our tool to find what pitches are most successful after the pitch you just threw."
)

st.write("**Disclaimer:** Data is sourced from the last 3 years of Statcast data.")

# Dropdowns for filters
prev_pitch_type = st.selectbox(
    "Select Previous Pitch Type",
    options=data['pitch_type'].unique() if 'pitch_type' in data.columns else [],
    index=0
)

pitcher_hand = st.selectbox(
    "Select Pitcher Handedness",
    options=data['p_throws'].unique() if 'p_throws' in data.columns else [],
    index=0
)

hitter_hand = st.selectbox(
    "Select Hitter Handedness",
    options=data['stand'].unique() if 'stand' in data.columns else [],
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

# Prepare table for display without index column
table_data = pitch_success[['Rank', 'Pitch Type', 'Success Rate', 'Weighted Success Rate', 'Occurrences']].to_dict(orient='records')

# Display the table using st.table for better formatting
st.write("### Top 5 Ranked Pitch Recommendations")
st.table(table_data)

# Add a key below the table
st.write("### Key")
st.write(
    """
    - **Success Rate**: The percentage of times a pitch sequence resulted in a successful outcome 
      (e.g., strikeouts, swinging strikes, foul balls, called strikes, or balls hit under 80 mph exit velocity).
    - **Weighted Success Rate**: Adjusted success rate accounting for small sample sizes by factoring in 
      the global average success rate and a minimum sample size threshold.
    - **Occurrences**: The number of times the selected pitch sequence occurred in the last 3 years.
    """
)

# Add a glossary of pitch types based on Baseball Savant definitions
st.write("### Glossary of Pitch Types")
st.write(
    """
    - **Four-Seam Fastball (FF)**: A high-velocity pitch thrown with backspin, resulting in minimal movement and a straight trajectory.
    - **Slider (SL)**: A breaking pitch that combines the velocity of a fastball with the movement of a curveball. Exhibits sharp, late horizontal break.
    - **Curveball (CU)**: A slower pitch with significant downward movement caused by topspin. Follows a looping trajectory to deceive hitters.
    - **Changeup (CH)**: An off-speed pitch designed to mimic a fastball but thrown at a reduced velocity to disrupt timing.
    - **Splitter (FS)**: A pitch that appears similar to a fastball but drops sharply near the plate due to a "split-finger" grip.
    - **Sinker (SI)**: A fastball variant with heavy downward and horizontal movement, designed to induce ground balls.
    - **Cutter (FC)**: A fastball with late movement, slightly breaking away from the pitcher's arm side.
    - **Knuckle Curve (KC)**: A curveball thrown with a grip that reduces spin, combining knuckleball and curveball movement.
    - **Knuckleball (KN)**: A pitch with minimal spin, causing erratic movement due to air resistance.
    - **Sweeper (SV)**: A slider variant with an exaggerated horizontal break across the plate.
    - **Sweeping Curve (ST)**: A curveball with added horizontal movement alongside its vertical drop.
    - **Slow Curve (CS)**: A slower version of the curveball, emphasizing significant break and a looping trajectory.
    """
)
