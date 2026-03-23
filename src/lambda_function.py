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
    url= f"https://api.telegram.org/bot{token}"
    file_url= f"https://api.telegram.org/file/bot{token}"
    return url, file_url

def lambda_handler(event, context):
    # print(event)
    body= json.loads(event.get('body',{}))
    message= body.get('message',{})
    chat_id= message.get('chat').get('id')
    #username= message.get('from').get('first_name').get('last_name')
    photo_list= message.get('photo',[])

    if not photo_list:
        text_url= f"{url}/send_message"
        text_payload={
            "chat_id":chat_id,
            "text":"Please send me photo!I resizes images only"
        }
        send_photo_list_resp= request(method= "GET",url= text_url, data= text_payload)
        if send_photo_list_resp.status_code not in [200, 201, 203, 204]:
            return{"message":"Response of image not found", "status_code":500}
        return{"message":"image not found", "status_code":200}

    caption= body.get('message',{}).get('caption')
    if not caption:
        caption_url = f"{url}/send_caption"
        caption_text = "Please send me caption so that i can resize my image"
        send_caption_resp = request(method="GET", url=caption_url, data=caption_text)
        if send_caption_resp.status_code not in [200, 201, 203, 204]:
            return{"message":"send caption response not worked", "status_code":500}
        return{"message":"Dont get caption", "status_code":200}


    match= re.search(r"(\d+)\s*mb", caption.lower())
    if not match:
            return{"message":"doesnt match with caption", "status_code":400}
    resizing_mb = int(match.group(1))
    print(f"message:got value{resizing_mb}, status_code:200")
    
    if not photo_list or not chat_id:
        return{"message":"neither image nor chat_id found","status_code":400}
    file_id= photo_list[-1].get('file_id')  
    url, file_url = get_url()
    file_path_url= f"{url}/getFile?file_id={file_id}"
    print(f"file_path_url:{file_path_url}")
    path_resp= request(method="GET",url=file_path_url)
    print(f"path_response:{path_resp}")
    path_data= path_resp.json()
    print(f"path_data:{path_data}")
    file_path= path_data.get('result',{}).get('file_path')
    print(f"file_path:{file_path}")
    if not file_path:
         return{f"Not found file:{file_path},status_code:400"}
    
    download_url= f"{file_url}/{file_path}"
    print(f"download_url:{download_url}")
    image_resp =request(method="GET",url=download_url)
    print(f"image_resp:{image_resp}")

    image_bytes= image_resp.content
   # print(f"image_bytes:{image_bytes}")
    size_value= 1024*1024

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
            
    
    send_url= f"{url}/sendPhoto"
    print(f"send_url:{send_url}")
    fields= {
        'chat_id': str(chat_id),
        'caption': 'Here is your resized image!'
     }
    files= {'photo':(('image.jpg', output_buffer, 'image/jpeg'))}
    send_resp= request(method= "POST",url=send_url,data=fields,files= files)
    print(f"send_resp:{send_resp}")
    return{
        'status_code':200,
        'message':'success'
    }
    

    

if __name__ == "__main__":
    sample_event = {}
    with open("src\\sample_event.json","r") as f:
        sample_event = json.loads(f.read())
    token = ""
    with open("src\\variables.json", "r") as f:
        token_data = json.loads(f.read())
        token = token_data.get("token")
    os.environ["BOT_TOKEN"] = token
    
    lambda_handler(sample_event, None)