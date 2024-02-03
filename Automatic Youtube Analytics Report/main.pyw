from googleapiclient.discovery import build
import functions as func

# ------------------------------------------------------------------ #
# CONSTANTS                                                    
# ------------------------------------------------------------------ #

JSON_DATA = func.get_json_data("JSON Files//data_id.json")

API_KEY = JSON_DATA["api_key"]
PLAYLIST_ID = JSON_DATA["playlist_id"]
GMAIL_PASS = JSON_DATA["gmail_pass"]


YOUTUBE_SECRET_FILE = "JSON Files//youtube_oa.json"
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# ------------------------------------------------------------------ #
# Getting Credentials and Building Service
# ------------------------------------------------------------------ #

# Getting Credentials
youtube_credentials = func.get_credentials(SCOPES=YOUTUBE_SCOPES, CLIENT_SECRETS_FILE=YOUTUBE_SECRET_FILE)

# Building Youtube Service
youtube_service = build('youtube', 'v3', developerKey=API_KEY)
youtube_analytics_service = build('youtubeAnalytics', 'v2', credentials=youtube_credentials)


# ------------------------------------------------------------------ #
# Sending the request to get the Data and Executing 
# ------------------------------------------------------------------ #

# Extracting the Friday to Friday week in a yyyy-mm-dd format
start_date, end_date = func.get_previous_friday_to_friday()

# Getting the videos ID & title respc.
video_ids_titles = func.get_video_ids(youtube_service, PLAYLIST_ID)

# Sending the request to get data and executing
request = youtube_analytics_service.reports().query(
    ids="channel==MINE",
    startDate=start_date,
    endDate=end_date,
    metrics="views,estimatedMinutesWatched",
    dimensions="video",
    filters=f"video=={','.join([video_id[0] for video_id in video_ids_titles])}"

)

response = request.execute()

# ------------------------------------------------------------------ #
# Manipulation the data the extract Valuable informations
# ------------------------------------------------------------------ #

video_data = response['rows'] # Extracting all the data

# Combining two dictionnaries that have respc the keys: {"id", "title"} and {"id", "views", "watch_time"}
video_dict_1 = [{"id":elt[0], "title":elt[1]} for elt in video_ids_titles] 
video_dict_2 = [{"id":elt[0], "views":elt[1], "watch_time":elt[2]} for elt in video_data] 

merged_video_data = []

for dict1 in video_dict_1:
    for dict2 in video_dict_2:
        if dict1["id"] == dict2["id"]:
            merged_dict = {**dict1, **dict2}
            merged_video_data.append(merged_dict)
            break


# ------------------------------------------------------------------ #
# Generating the message to send via GMail 
# ------------------------------------------------------------------ #

message_report = func.generate_message(merged_video_data)

email_subject = "Report of the Week: " + start_date + " - " + end_date 
email_body = message_report

from_email = "...@gmail.com" # Sender Email
to_email = "...@gmail.com" # Receiver Email

func.send_email(email_subject, email_body, from_email, to_email, GMAIL_PASS) 


