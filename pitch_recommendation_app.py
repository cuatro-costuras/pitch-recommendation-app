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
        # Debugging: Print chunk columns
        print(f"Chunk columns: {chunk.columns.tolist()}")

        if 'year' in chunk.columns:
            filtered_chunk = chunk[chunk['year'] >= year_filter]
            if not filtered_chunk.empty:
                filtered_chunks.append(filtered_chunk)

    if filtered_chunks:
        filtered_data = pd.concat(filtered_chunks, ignore_index=True)
    else:
        print("No data matched the filtering criteria.")
        filtered_data = pd.DataFrame(columns=['pitch_type', 'p_throws', 'stand', 'events', 'description', 'launch_speed', 'year'])

    # Map pitch types to full names
    if 'pitch_type' in filtered_data.columns:
        filtered_data['pitch_type'] = filtered_data['pitch_type'].map(pitch_type_mapping).fillna('Unknown')
        filtered_data = filtered_data[filtered_data['pitch_type'] != 'Unknown']

    return filtered_data

# Load the filtered dataset
data = load_filtered_data('smaller_statcast.csv', year_filter=2021)

# Check if the dataset is empty
if data.empty:
    st.warning("The dataset is empty or does not match the filtering criteria.")
    data = pd.DataFrame({
        'pitch_type': ['Four-Seam Fastball', 'Slider', 'Changeup'],
        'p_throws': ['R', 'L'],
        'stand': ['R', 'L'],
        'events': [],
        'description': [],
        'launch_speed': [],
        'year': []
    })

# Add success criteria
if not data.empty:
    data['success'] = (
        (data['events'] == 'strikeout') |
        (data['description'] == 'swinging_strike') |
        (data['description'] == 'foul') |
        (data['description'] == 'called_strike') |
        ((data['launch_speed'] < 80) & (data['launch_speed'].notna()))
    )
    data['prev_pitch_type'] = data['pitch_type'].shift(1)

# Streamlit App
st.title("Pitch Sequence Success Rates")

# Add description
st.write(
    "Have you ever been in the middle of an at-bat and wondered what pitch to throw next? "
    "Use our tool to find what pitches are most successful after the pitch you just threw."
)

st.write("**Disclaimer:** Data is sourced from the last 3 years of Statcast data.")

# Dropdowns for filters
if 'pitch_type' in data.columns and not data['pitch_type'].isnull().all():
    prev_pitch_type = st.selectbox(
        "Select Previous Pitch Type",
        options=data['pitch_type'].unique(),
        index=0
    )
else:
    prev_pitch_type = st.selectbox(
        "Select Previous Pitch Type",
        options=["Four-Seam Fastball", "Slider", "Changeup"],
        index=0
    )

if 'p_throws' in data.columns and not data['p_throws'].isnull().all():
    pitcher_hand = st.selectbox(
        "Select Pitcher Handedness",
        options=data['p_throws'].unique(),
        index=0
    )
else:
    pitcher_hand = st.selectbox(
        "Select Pitcher Handedness",
        options=["R", "L"],
        index=0
    )

if 'stand' in data.columns and not data['stand'].isnull().all():
    hitter_hand = st.selectbox(
        "Select Hitter Handedness",
        options=data['stand'].unique(),
        index=0
    )
else:
    hitter_hand = st.selectbox(
        "Select Hitter Handedness",
        options=["R", "L"],
        index=0
    )

# Filter data based on selections
filtered_data = data[
    (data['prev_pitch_type'] == prev_pitch_type) &
    (data['p_throws'] == pitcher_hand) &
    (data['stand'] == hitter_hand)
]

# Group by pitch type and calculate success rate
if not filtered_data.empty:
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

    # Prepare table for display
    st.write("### Top 5 Ranked Pitch Recommendations")
    st.table(pitch_success[['Rank', 'Pitch Type', 'Success Rate', 'Weighted Success Rate', 'Occurrences']])
else:
    st.warning("No data available for the selected filters.")

# Add a key
st.write("### Key")
st.write(
    """
    - **Success Rate**: The percentage of times a pitch sequence resulted in a successful outcome.
    - **Weighted Success Rate**: Adjusted success rate accounting for small sample sizes.
    - **Occurrences**: The number of times the selected pitch sequence occurred.
    """
)
