Link to my YouTube Channel: https://www.youtube.com/channel/UCeNWB5QgkL4iQXCAz68zpbg

The main structure of the Projects is as follows:

Automatic Report
JSON Files
- data_id.JSON
- youtube_oa.JSON

tokens

youtube_token.pickle 

functions.py

main.pyw (extension .pyw to disable command line popping up)

information.txt



JSON Files:

Is a folder that contains all the JSON files used in the Project

- `data_id.JSON`:
Is a self made JSON files that keeps track of APIs and relevant IDs that were
not automatically generated. It has the following items

    "api_key": an API like key generated from google console,
    "playlist_id": an ID from the youtube channel. To get it replace your channel ID after list=... if any of your channels playlists https://www.youtube.com/playlist?list=
    "gmail_pass": SMTP code generated from authentification


- `youtube_oa`:
This file is generated when creating OAuth credentials in google developer console
