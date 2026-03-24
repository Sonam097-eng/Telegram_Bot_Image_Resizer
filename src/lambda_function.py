import json
import os
from requests import request
import io
from PIL import Image
import re


resizing_mb= ""

def get_token():
    token = os.environ.get("BOT_TOKEN")
    return token

def get_url():
    token= get_token()
    base_url = "https://api.telegram.org"
    url= f"{base_url}/bot{token}"
    file_url= f"{base_url}/file/bot{token}"
    return url, file_url

def call_telegram(method, url, data=None, files=None, headers=None, params=None):
    print(f"Sending a request with method: {method} to url: {url}")
    try:
        resp = request(method = method, url= url, data= data, files= files, headers=headers, params=params)
        print(f"Got response : {resp.text}")
        if resp.status_code not in [200, 201, 202, 203, 204]:
            return {
                "status": False,
                "resp" : resp,
                "status_code" : resp.status_code
            }
        return{
            "status": True,
            "resp": resp,
            "status_code": resp.status_code
        }
        
    except Exception as e:
        return {
                "status": False,
                "resp": e,
                "status_code": None
            } 
    

def resizing_image(image_bytes, size_value):

    with Image.open(io.BytesIO(image_bytes))as image:
        quality= 95
        while quality > 10:
            output_buffer= io.BytesIO()
            image.save(output_buffer,format='JPEG',quality= quality, optimize= True)
            if len(output_buffer.getvalue()) < size_value:
                output_buffer.seek(0)
                break
            quality -= 5
            output_buffer.seek(0)
    return output_buffer       
    
def send_message_to_user(chat_id, drafted_message):
    text_payload={
            "chat_id":chat_id,
            "text": drafted_message
        }
    url, _ = get_url()
    text_url= f"{url}/sendMessage"
    method = "GET"
    print(f"Calling with chat_id: {chat_id}, method : {method}, url: {text_url} for send drafted message: {drafted_message}")
    resp = call_telegram(method, text_url, data=text_payload)
    if not resp.get("status"):
        print(f"Something went wrong while sending resp to user for url: {text_url}")
        return{"message": resp.get("resp").json(), "status_code": 500 if not resp.get("status_code") else resp.get("status_code")}
        #if not resp.get("status"):
         #       return{"message": resp.get("resp"), "status_code": 500 if not resp.get("status_code") else resp.get("status_code")}    
    return {"message":"Image not found", "status_code":200}
    

def lambda_handler(event, context):
    # print(event)
    body= json.loads(event.get('body',{}))
    message= body.get('message',{})
    chat_id= message.get('chat').get('id')
    if not chat_id:
        print("Something went wrong for Photo or chat id not found")
        return{"message":"chat_id not found","status_code": 404}
    
    #username= message.get('from').get('first_name').get('last_name')
    photo_list= message.get('photo',[])
    url, file_url = get_url()

    if not photo_list:
        return send_message_to_user(chat_id=chat_id, drafted_message="Please send me photo!I resizes images only")
                           
    caption= body.get('message',{}).get('caption')
    if not caption:
        return send_message_to_user(chat_id=chat_id, drafted_message="Please send me caption so that i can resize my image")
        
    match= re.search(r"(\d+)\s*mb", caption.lower())
    if not match:
        return send_message_to_user(chat_id=chat_id, drafted_message="'mb' keyword in caption not found! Please provide a size under which you want to resize the imamge eg. 1 mb") 
        
    resizing_mb = int(match.group(1))
    print(f"Got resizing size: {resizing_mb}")
    
    file_id = photo_list[-1].get('file_id')  
    file_path_url= f"{url}/getFile?file_id={file_id}"
    
    resp = call_telegram("GET", file_path_url)
    if not resp.get("status"):
        print("Something went wrong while getting file_path of image")
        send_message_to_user(chat_id=chat_id, drafted_message="Something Went wrong while getting Image from Telegram")
        return {"message": resp.get("resp").json(), "status_code": 500 if not resp.get("status_code") else resp.get("status_code")}    

    print(f"path_response:{resp}")
    path_data = resp.get("resp")
    path_data = path_data.json()
    file_path= path_data.get('result',{}).get('file_path')
        
    if not file_path:
        send_message_to_user(chat_id=chat_id, drafted_message=f"Something Went wrong while processing file_path from telegram")
        return {"message": f"Not found file: {file_path}", "status_code": 404}
    
    download_url= f"{file_url}/{file_path}"
    
    resp = call_telegram("GET", download_url)
    if not resp.get("status"):
        send_message_to_user(chat_id=chat_id, drafted_message="Something Went wrong while downloading image to resize")
        return {"message": resp.get("resp"), "status_code": 500 if not resp.get("status_code") else resp.get("status_code")}    

    image_bytes= resp.get("resp").content
    # print(f"image_bytes:{image_bytes}")

    size_value = resizing_mb
    output_buffer = resizing_image(image_bytes, size_value )
    send_url= f"{url}/sendPhoto"
    print(f"send_url:{send_url}")
    fields= {
            'chat_id': str(chat_id),
            'caption': 'Here is your resized image!'
        }
    files= {'photo':(('image.jpg', output_buffer, 'image/jpeg'))}
    resp= call_telegram("POST", send_url, data=fields, files=files)
    print(f"send_resp:{resp}")
    if not resp.get("status"):
        send_message_to_user(chat_id= chat_id, drafted_message="Something went wrong while sending the resized image to user")
        return{"message": resp.get("resp").json(), "status_code": 500 if not resp.get("status_code") else resp.get("status_code")}
    print("Processing completed!")
    return {"message":"Data found", "status_code":200}

        

    

if __name__ == "__main__":
    sample_event = {}
    with open("src\\sample_event.json","r") as f:
        sample_event = json.loads(f.read())
    token = ""
    with open("src\\variables.json", "r") as f:
        token_data = json.loads(f.read())
        token = token_data.get("token")
    os.environ["BOT_TOKEN"] = token
    
    return_result = lambda_handler(sample_event, None)
    print(f"returned result: {return_result}")