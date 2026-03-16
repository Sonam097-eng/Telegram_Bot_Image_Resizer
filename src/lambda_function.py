import json
import boto3
import urllib3
import os
import requests
from dotenv import load_dotenv
load_dotenv()

# Configuration
TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Initialize resources
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TelegramBotData')

def lambda_handler(event, context):
    try:
        print(f"Starting Processing")
        body = json.loads(event['body'])
        message = body.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        user_name = message.get('from', {}).get('first_name', 'User')

        if not chat_id:
            return {"statusCode": 200}
            
        # Load the layer now that we know we have a valid webhook
        from io import BytesIO
        from PIL import Image    

        reply_text = None # Default to None so we don't send duplicate messages

        # 1. Logic: Detect Image vs Text
        if 'photo' in message:
            print(f"Got a photo")
            # Telegram sends an array of photo sizes. The last one is the largest.
            file_id = message['photo'][-1]['file_id']
            
            # Step A: Get the file path from Telegram
            get_file_url = f"{BASE_URL}/getFile?file_id={file_id}"
            file_resp = requests.request(method='GET', url=get_file_url)
            file_data = file_resp.json()
            
            if file_data.get('ok'):
                file_path = file_data['result']['file_path']
                download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                print(f"Downloading image from: {download_url}")
                
                # Step B: Download the actual image bytes into memory
                image_response = requests.request(method='GET', url=download_url)
                image_bytes = image_response.json()
                
                print("Resizing image with Pillow...")
                # Step C: Open and resize the image using Pillow
                with Image.open(BytesIO(image_bytes)) as img:
                    # Resize to max 500x500 pixels, maintaining aspect ratio
                    img.thumbnail((500, 500)) 
                    
                    output_buffer = BytesIO()
                    img_format = img.format if img.format else 'JPEG'
                    img.save(output_buffer, format=img_format)
                    output_buffer.seek(0) 

                print("Uploading resized photo back to Telegram...")
                # Step D: Send the resized photo back to Telegram
                send_photo_url = f"{BASE_URL}/sendPhoto"
                
                requests.request(
                    method='POST', 
                    url=send_photo_url,
                    data={
                        'chat_id': str(chat_id),
                        'photo': ('resized_image.jpg', output_buffer.read(), 'image/jpeg'),
                        'caption': 'Here is your resized image! 📸'
                    }
                )
                print("Photo sent successfully!")
                
            else:
                reply_text = "Failed to retrieve image path from Telegram."
                
        else:
            print(f"Got a text")
            # Handle standard text
            user_text = message.get('text', '')
            reply_text = f"You said: {user_text}\n\nTo resize an image, please send it as a 'Photo'."
            print(f"user_text:{user_text}")  

        # 2. Increment DynamoDB count
        response = table.update_item(
            Key={'user_id': str(chat_id)},
            UpdateExpression="ADD msg_count :val SET first_name = :n",
            ExpressionAttributeValues={':val': 1, ':n': user_name},
            ReturnValues="UPDATED_NEW"
        )
        current_count = response['Attributes']['msg_count']

        # 3. Send the standard text reply ONLY if it's text (or an error)
        if reply_text:
            final_msg = f"{reply_text}\n\n(Total messages: {current_count})"
            print(f"Sending reply: {final_msg}")
            send_url = f"{BASE_URL}/sendMessage"
            payload = {"chat_id": chat_id, "text": final_msg}
            
            answer_reply = requests.request(method="POST", url=send_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
            print(f"Telegram response: {answer_reply.json}")

        return {"statusCode": 200}

    except Exception as e:
        print(f"Error: {str(e)}")
        
        # Clever Debugging: Tell the bot to message you the exact error!
        try:
            error_msg = f"⚠️ Oops, I crashed! Here is the error:\n\n{str(e)}"
            send_url = f"{BASE_URL}/sendMessage"
            error_payload = {"chat_id": chat_id, "text": error_msg}
            http.request("POST", send_url, 
                         body=json.dumps(error_payload), 
                         headers={'Content-Type': 'application/json'})
        except:
            pass 
            
        return {"statusCode": 200}