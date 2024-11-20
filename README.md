# pitch-recommendation-app

Have you ever been in the middle of an at-bat and wondered what pitch to throw next? This **Streamlit app** uses data from the last three years of Statcast to analyze pitch sequences and provide recommendations based on success rates. The app is designed to help pitchers and coaches make informed decisions during games.

## Features
- Select the previous pitch type, pitcher handedness, and hitter handedness.
- View the top 5 pitch recommendations ranked by weighted success rate.
- Success metrics include strikeouts, swinging strikes, foul balls, called strikes, and weak contact (exit velocity < 80 mph).
- Glossary of pitch types with Baseball Savant definitions.

## How to Use
1. Open the app using the provided link.
2. Select your desired filters (e.g., previous pitch type, handedness).
3. View the ranked recommendations and success metrics.

## Data Source
This app uses subset of Statcast data from the last three years. 

## Technologies Used
- **Python**
- **Streamlit**
- **Pandas**
- **Matplotlib**

## About
This app was created to assist pitchers and coaches by providing data-driven recommendations for pitch sequencing.
