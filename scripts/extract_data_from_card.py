import requests
import os
import json
import glob
import output_generator as og

def load_config():
    with open(os.path.dirname(__file__) + "/../config.json", 'r') as fp:
        config = json.load(fp)
    
    api_key = config['trello-api-key']
    api_token = config['trello-private-token']
    board_id = config['trello-board-id']
    return api_key, api_token, board_id


def get_trello_list(query, board_id):
    '''
    Get the lists from trello board
    '''
    url = f"https://api.trello.com/1/boards/{board_id}/lists"

    response = requests.request(
       "GET",
        url,
        params=query
    )

    trello_lists = json.loads(response.text)

    return trello_lists


def get_first_card_from_list(query, list_id):
    '''
    Get the first card from IN List
    '''
    url = f"https://api.trello.com/1/lists/{list_id}/cards"

    response = requests.request(
       "GET",
        url,
        params=query
    )
    id = json.loads(response.text)[0]["id"]
    name = json.loads(response.text)[0]["name"]
    return id, name


def get_attachments_from_card(query, card_id):
    url = f"https://api.trello.com/1/cards/{card_id}/attachments"

    headers = {
        "Accept": "application/json"
    }
    
    response = requests.request(
        "GET",
        url,
        headers=headers,
        params=query
    )

    attachments = json.loads(response.text)
    return attachments



def validate_attachments(attachments):
    validated_attachments = []
    
    is_exists = False
    for attachment in attachments:
        file_name = attachment["fileName"]
        download_url = attachment["url"]

        if isinstance(file_name, str):
            is_exists = True
            if file_name.endswith(".mp3") or file_name.endswith(".wav"):
                validated_attachments.append({"fileName": file_name, "url": download_url})
    
    if len(validated_attachments) == 0 and is_exists:
        return False
    
    return validated_attachments


def download_attachments(attachments, key, token):
    for attachment in attachments:
        download_url = attachment["url"]
        file_name = attachment["fileName"]
        
        
        print("\nDownloading file")
        authorization = f'OAuth oauth_consumer_key="{key}", oauth_token="{token}"'
        headers = { 'Authorization': authorization }
        response = requests.get(download_url, headers=headers, allow_redirects=True)


        #removing all the files in directory
        curr_dir = os.path.dirname(__file__) + "/../attachments"
        files = glob.glob(f"{curr_dir}/*")
        
        for file in files:
            os.remove(file)
        #saving the file
        with open(f"{curr_dir}/{file_name}", 'wb') as fp:
            fp.write(response.content)
            print(f"Saving {file_name} done")




def move_card(query, list_id, card_id):
    url = f"https://api.trello.com/1/cards/{card_id}"

    headers = {
        "Accept": "application/json"
    }

    query["idList"] = list_id

    response = requests.request(
        "PUT",
        url,
        headers=headers,
        params=query
    )

    if(response.ok):
        print("\nCard moving successful")
    else:
        print("\nCard moving failed")


def upload_attachment(query, card_id):
    url = f"https://api.trello.com/1/cards/{card_id}/attachments"
    headers = {
        "Accept": "application/json"
    }

    files = glob.glob(os.path.dirname(__file__) + "/../outputs/*")

    for file in files:
        file_name = file.split("\\")[-1]
        print(f"Uploading {file_name}")
        fp = open(file, 'rb')

        files = {
            'file': (file_name, fp),
        }
        response = requests.request(
            "POST",
            url,
            headers=headers,
            params=query,
            files=files
        )
        fp.close()
        if response.ok:
            print(f"\n{file_name} upload successful")
        else:
            print(f"\nError: {response.reason}")



def create_error_card(query, error_list_id, name, desc):

    url = "https://api.trello.com/1/cards"
    headers = {
        "Accept": "application/json"
    }
    query['idList'] = error_list_id
    query['name'] = name
    query['desc'] = desc

    response = requests.request(
        "POST",
        url,
        headers=headers,
        params=query
        )
    
    if response.ok:
        print("\nError card added to error list")
    else:
        print("\nError adding error card to list")


def generate_attachments(model):

    audio_file = glob.glob(os.path.dirname(__file__) + "/../attachments/*")[0]
    og.generate_transcribe(model, audio_file)
    og.generate_translation(model, audio_file)
    og.generate_video(audio_file)


def main(model):
    api_key, api_token, board_id = load_config()
    query = {
            'key': api_key,
            'token': api_token
            }

    trello_lists = get_trello_list(query, board_id)
    IN_list = None
    Process_list = None
    Out_list = None
    Error_list = None

    for list in trello_lists:
        if list['name'].lower() == 'in':
            print("IN card received")
            IN_list = list
        elif list['name'].lower() == 'process':
            Process_list = list
            print("Process card received")  
        elif list['name'].lower() == 'out':
            Out_list = list
            print("Out card received")  
        elif list['name'].lower() == 'errors':
            Error_list = list
            print("Error card received")  

    if IN_list:
        IN_list_id = IN_list["id"]
        IN_list_first_card_id, _ = get_first_card_from_list(query, IN_list_id)
        attachments = get_attachments_from_card(query, IN_list_first_card_id)
        validated_attachments = validate_attachments(attachments)

        if validated_attachments == False:
            print("\nNo valid attachment found")
            if Error_list:
                error_list_id = Error_list['id']
                create_error_card(query, error_list_id, "Attachment Error", "No valid attachment found")

        elif len(validated_attachments):
            download_attachments(validated_attachments, api_key, api_token)
            Process_list_id = Process_list["id"]
            Out_list_id = Out_list["id"]
            move_card(query, Process_list_id, IN_list_first_card_id)
            generate_attachments(model)
            upload_attachment(query, IN_list_first_card_id)
            move_card(query, Out_list_id, IN_list_first_card_id)

            try:
                final_video = os.path.dirname(__file__) + "/../outputs/Video_with_subtitle.mp4"
                print("\nDeleting the final video")
                os.remove(final_video)
                print("Done deleting the final video")
            except Exception as e:
                print(str(e))

        else:
            print("\nNo attachment found")
    else:
        print("\nNo IN list found")


# if __name__ == "__main__":
#     main()