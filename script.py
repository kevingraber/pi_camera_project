from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaFileUpload
import datetime 
import os
import config
from time import sleep

# Setup the Drive v3 API
SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('drive', 'v3', http=creds.authorize(Http()))
# ----------------------

# ID of our Google Drive project directory
root_drive_dir = config.root_id

# Get & format current date - ex: 17-06-2018
date_today = datetime.date.today().strftime('%d-%m-%Y')

# Drive folder files will be uploaded to
drive_target_folder = None

# Creates a new folder with specified name, parents & returns the folder's id
def create_drive_folder(name, parent_folder):
    file_metadata = {
        'name': name,
        'parents': [parent_folder],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = service.files().create(body=file_metadata, 
                                  fields="id").execute()
    return file.get('id')

# Search Drive for folder w/ given name - create folder if it doesn't exist and update drive_target_folder
res = service.files().list(q="name='%s'" % date_today).execute()
if ( len(res['files']) == 0 ):
    drive_target_folder = create_drive_folder(date_today, root_drive_dir)
else:
    drive_target_folder = res['files'][0]['id']

# Local folder to scan for changes
local_target_folder = None

# lists to keep track of files
files_before = []
files_after = []

# If we don't have a directory for the current date, create one
if not os.path.exists(date_today):
    print("Directory '%s' does not exist creating.." % date_today)
    os.makedirs(date_today)

# Change directory to folder for date_today's date
local_target_folder = date_today

def upload_file(file, dir_id):
    print('Uploading %s...' % file)
    file_metadata = {
        'name': '%s' % file,
        'parents': [dir_id]
    }
    media = MediaFileUpload('%s/%s' % (local_target_folder, file), mimetype='image/jpeg')
    file = service.files().create(body=file_metadata, 
                                  media_body=media, 
                                  fields='id').execute()

while True:

    # New day? -> update date_today, create and point to new local/drive folders
    new_time = datetime.date.today().strftime('%d-%m-%Y')
    if (date_today != new_time):
        date_today = new_time
        drive_target_folder = create_drive_folder(date_today, root_drive_dir)
        os.makedirs(date_today)
        local_target_folder = date_today
        files_before = []

    # Scan local folder for files & determine if new files are present
    files_after = os.listdir(local_target_folder)
    delta = set(files_after).symmetric_difference(files_before)

    # If there are new files...
    if (len(delta) > 0):

        print("New files detected:")
        print(delta)

        # Scan drive folder for files
        query_results = service.files().list(q="'%s' in parents" % drive_target_folder).execute()
        drive_files = query_results['files']
        print(drive_files)

        files_to_upload = list(delta.symmetric_difference(drive_files))
        print("We need to upload the following files..")
        print(files_to_upload)
        for img in files_to_upload:
            upload_file(img, drive_target_folder)

    # Reset files_before list and sleep for wait a minute
    files_before = files_after
    sleep(60)
