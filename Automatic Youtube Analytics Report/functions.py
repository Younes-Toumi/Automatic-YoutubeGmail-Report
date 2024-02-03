import os
import pickle
import json
import smtplib

import numpy as np 
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from email.mime.text import MIMEText
from datetime import datetime, timedelta

def get_credentials(SCOPES: list, CLIENT_SECRETS_FILE: str):

    """
    Retrieves or generates YouTube API credentials.

    This function checks for the presence of existing credentials. If found,
    it loads them from the designated file. If not found or if the credentials
    are invalid or expired, it initiates the OAuth 2.0 flow to obtain new
    credentials, prompting the user for consent if necessary.

    Parameters:
    - SCOPES (list): A list of scopes required for accessing the YouTube API.
    - CLIENT_SECRETS_FILE (str): The path to the client secrets file containing
                                  the OAuth 2.0 client ID and client secret.

    Returns:
    - credentials: The authorized credentials required for YouTube API requests.
    """


    credentials = None

    # Check if there are existing credentials saved in a file
    if os.path.exists("tokens\\youtube_token.pickle"):
        print('Loading YouTube Credentials From File...')
        with open("tokens\\youtube_token.pickle", "rb") as token:
            credentials = pickle.load(token)
    
    # If no credentials found or if they are invalid or expired, initiate OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:

            # Initialize OAuth flow using client secrets file
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES
            )

            # Run a local server to obtain user consent for accessing YouTube API
            flow.run_local_server(port=0, prompt='consent',
                                authorization_prompt_message='')
            credentials = flow.credentials

            # Save the credentials for the next run
            with open('tokens//youtube_token.pickle', 'wb') as f:
                print('Saving Youtube Credentials for Future Use...')
                pickle.dump(credentials, f)

    return credentials


def get_json_data(file_path: str) -> dict:

    """
    Reads JSON data from a file and returns it as a Python dictionary.

    This function opens the specified JSON file and loads its content into
    a Python dictionary, which is then returned to the caller.

    Parameters:
    - file_path (str): The path to the JSON file to be read.

    Returns:
    - json_data (dict): The JSON data stored in the file as a dictionary.
    """

    with open(file_path, "r") as json_file:
       json_data = json.load(json_file)

    
    return json_data


def get_video_ids(youtube, playlist_id: str) -> list:

    """
    Retrieves video IDs and titles from a YouTube playlist.

    This function queries the YouTube Data API to fetch video IDs and titles
    from the specified playlist. It iterates through paginated results until
    all videos in the playlist are retrieved.

    Parameters:
    - youtube: An authenticated instance of the YouTube Data API service.
    - playlist_id (str): The ID of the YouTube playlist from which to fetch videos.

    Returns:
    - video_ids_titles (list): A list of lists containing video IDs and titles
                               extracted from the playlist.
    """


    def get_video_response(youtube, playlist_id, next_page_token=None):
        """
        This nested function sends a request to the YouTube Data API to obtain
        a response containing video items from the specified playlist.
        """
        
        request = youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token

            
        )

        response = request.execute()

        return response
    
    # Initial request to fetch video items
    response = get_video_response(youtube, playlist_id)
    
    video_ids_titles = []

    # Iterate through paginated results until all videos are retrieved
    while True:

        try:
            # Check if there is a next page available
            assert(response['nextPageToken'])

            # Extract video IDs and titles from current page
            for elt in response['items']:
                video_id = elt['contentDetails']['videoId']
                video_title = elt['snippet']['title']
                video_ids_titles.append([video_id, video_title])
            
            # Fetch next page of results
            next_page_token = response['nextPageToken']
            response = get_video_response(youtube, playlist_id, next_page_token)

        except:
            # No next page found, return current content
            
            # Extract video IDs and titles from current page
            for elt in response['items']:
                video_id = elt['contentDetails']['videoId']
                video_title = elt['snippet']['title']

                video_ids_titles.append([video_id, video_title])

            break

    return video_ids_titles


def generate_message(merged_video_data: dict) -> str:

    """
    Basic function that aims to generate a report based on a dictionnary (top 3 videos).

    Parameters:
    - merged_video_data (dict): of the form:
        {
            "id":           [id_1, id_2, ...],
            "title":        [title_1, title_2, ...],
            "views":        [view_1, view_2, ...],
            "watch_time":   [wt_1, wt_2, ...]
                            }

    `merged_video_data` is a dictionnary that contains all the youtube video data to include
    in the report

    Returns:
    - message (str): That gives the weekly report in terms of views and watchtime, there display the top 3
    performing videos in terms of views and watch time (hours)
    """

    # Extracting Arrays from Dictionnary
    video_titles = np.array([item["title"] for item in merged_video_data])
    video_views = np.array([item["views"] for item in merged_video_data])
    video_watch_time = np.array([item["watch_time"] for item in merged_video_data])

    # Computing the Weekly results
    weekly_views = np.sum(video_views)
    weekly_watch_time = np.sum(video_watch_time)

    # Getting the top 3 videos for both Views and Watch time 
    top3_views_indices = np.argsort(video_views)[-3:][::-1] # Getting Descinding order
    top3_watch_time_indices = np.argsort(video_watch_time)[-3:][::-1]

    # Generating the message
    message = f"""
Weekly report of the Channel:
Views: {weekly_views} | Watch Hours: {weekly_watch_time/60:.2f}\n
    """
    message += "\nThe top 3 videos according to Views:\n"

    for i, views_idx in enumerate(top3_views_indices, start=1):
        message += f"\t - N°{i}: With {video_views[views_idx]} Views "
        message += f"({100*video_views[views_idx]/weekly_views:.2f} %) -> {video_titles[views_idx][:50]}...\n"


    message += "\nThe top 3 videos according to Watch Time:\n"

    for i, watch_time_idx in enumerate(top3_watch_time_indices, start=1):
        message += f"\t - N°{i}: With {video_watch_time[watch_time_idx]/60:.2f} h "
        message += f"({100*video_watch_time[watch_time_idx]/weekly_watch_time:.2f} %) -> {video_titles[watch_time_idx][:40]}...\n"

    return message



def send_email(subject: str, body: str, from_email: str, to_email: str, gmail_pass: str) -> None:
    """
    Send a message via GMail using the SMTP server, by using the `gmail_pass` to confirm 
    idendity, do not share the value of `gmail_pass`
    """
    # Create the email message
    msg = MIMEText(body)
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Connect to Gmail's SMTP server
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.ehlo()
        server.login(from_email, gmail_pass)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()


def get_previous_friday_to_friday():

    """
    A function that utilizes the `datetime` package in python, and returns two consicutive
    Fridays.

    Example: Suppose current day is 03/02/2024.

    >> get_previous_friday_to_friday()
    (2024-01-26, 2024-02-01)


    Returns:
    start_date_str (str), end_date_str (str): The two consicutive Fridays of the week when the script was
    executed in a YYYY-MM-DD format

    """

    # Get today's date
    today = datetime.now().date()

    # Find the day index of the current day (0=Monday, 1=Tuesday, ..., 6=Sunday)
    current_day_index = today.weekday()

    # Calculate the difference in index between the current day and Friday (4)
    days_past_friday = (current_day_index - 4) % 7

    # Calculate the previous Friday
    friday_end = today - timedelta(days=days_past_friday)

    # Calculate the end of the current week (next Friday)
    friday_start = friday_end - timedelta(days=7)

    # Format the dates in the 'yyyy-mm-dd' format
    start_date_str = friday_start.strftime('%Y-%m-%d')
    end_date_str = friday_end.strftime('%Y-%m-%d')

    return start_date_str, end_date_str