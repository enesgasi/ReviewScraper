# Steam Review Scraper

## Overview
Steam Review Scraper is a Streamlit-based application that fetches reviews of a specified game from Steam using its App ID. The extracted reviews can be saved in Word, JSON, or CSV formats.

## Features
- Fetches game reviews from Steam.
- Retrieves the game's name using its App ID.
- Saves reviews in different formats:
  - **Word (.docx)**
  - **JSON (.json)**
  - **CSV (.csv)**
- Provides a user-friendly Streamlit interface.
- Displays a loading animation while fetching data.
- Includes a direct link to find the App ID of games on SteamDB.

## Requirements
Before running the application, make sure you have the following installed:
- Python 3.x
- Required Python libraries:
  ```sh
  pip install streamlit requests beautifulsoup4 python-docx
  ```

## How to Run
1. Clone this repository or download the source code.
2. Navigate to the project directory.
3. Run the following command:
   ```sh
   streamlit run your_script.py
   ```
4. Open the provided URL in your browser.

## How to Use
1. Enter the Steam App ID of the game you want to fetch reviews for.
2. The application will display the game's name.
3. Click one of the buttons to save the reviews in your preferred format.
4. The generated file will be available for download directly from the interface.

## Notes
- If the App ID is invalid, the application will display a warning.
- The application fetches reviews from multiple pages but is limited to a certain number of pages for efficiency.
- Ensure you have a stable internet connection while fetching reviews.

## Future Enhancements
- Add a language selection feature to filter reviews by specific languages.
- Improve error handling and exception management.
- Support more file formats such as Excel.

## License




