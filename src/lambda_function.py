import json
import requests
import re
import io
import os
from PIL import Image



class TelegramBot:
    def __init__(self, token):
        if not token:
            print(f"Bot token is misssing")
            raise ValueError("Telegram bot doesnt work without token")

        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.file_url = f"https://api.telegram.org/file/bot{self.token}"

    def call_api(self, method, endpoint, data = None, files = None):
        url = f"{self.base_url}/{endpoint}"
        print(f"calling API:{url} with {method}")

        try:
            resp = requests.request(method = method, url = url, data= data, files= files)
            print(f"For URL: {url} got status_code: {resp.status_code} and response: {resp.text}")
            if resp.status_code in [200, 201, 202, 203, 204]:
                return{"status":True, "resp": resp.json(), "status_code": resp.status_code}
            return{"status":False, "resp":resp.json(), "status_code": resp.status_code}
        except Exception as e:
            return{"status":False, "resp":f"{str(e)}", "status_code":500}
        
    def send_message(self, chat_id, data):
        payload = {"chat_id": chat_id, "data": data}
        return self.call_api("POST", "sendMessage", data = payload)
    
    def send_photo(self, chat_id, photo_buffer, caption = ""):
        payload = {"chat_id": chat_id, "caption": caption }
        files= {"photo":("image.jpg", photo_buffer, "image/jpeg")}
        return self.call_api("POST", "sendPhoto",data= payload, files= files)
    
    def get_file(self, file_id):
        resp = self.call_api("GET", f"getFile?file_id={file_id}")
        if resp.get("status"):
            return resp["resp"].get("result", {}).get("file_path", {})
        return None
    
    def download_file(self, file_path):
        url = f"{self.file_url}/{file_path}"
        try:
            resp= requests.request("GET", url= url)
            if resp.status_code in [200, 201, 202, 203, 204]:
                return resp.content
        except Exception as e:
            print(f"Download failed :{e}")
        return None
    
class ImageResizer:

    @staticmethod
    def image_resizer(image_bytes, resized_mb):
        target_bytes= resized_mb*1024*1024

        with Image.open(io.BytesIO(image_bytes)) as f:
            quality = 95
            while quality > 10:
                output_buffer = io.BytesIO()
                f.save(output_buffer, format = "JPEG", quality= quality, optimize = True)

                if len(output_buffer.getvalue()) <= target_bytes:
                    output_buffer.seek(0)
                    return output_buffer
                quality -= 5
                output_buffer.seek(0)
                return output_buffer
class WebhookHandler:
    def __init__(self, bot: TelegramBot , resizer: ImageResizer):
        self.bot = bot
        self.resizer = resizer

    def process_event(self, event):
        body = json.loads(event.get("body", {}))
        message = body.get("message", {})
        chat_id = message.get("chat", {}).get("id", {})
        if not chat_id:
            print(f"No chat_id found")
            return{f"message": "chat_id not found", "status_code": 404}
        
        photo_list = message.get("photo", [])
        if not photo_list:
            self.bot.send_message(chat_id= chat_id, data = "Please send me a photo.So that that i can resize it." )
            return {f"message":"No photo provided", "status_code": 200}
        
        caption = message.get("caption", "")
        if not caption:
            self.bot.send_message(chat_id= chat_id, data = "Please send me a caption.So that that i can use it to resize photo." )
            return {f"message":"No caption provided", "status_code": 200}
        
        match = re.search(r"(\d+)\s*mb", caption.lower())
        resized_mb = int(match.group(1))
        print(f"target size:{resized_mb}")

        file_id = photo_list[-1].get("file_id")
        file_path = self.bot.get_file(file_id)

        if not file_path:
            self.bot.send_message(chat_id, "Dont get the image path")
            return {f"message":"not get file_path", "status_code": 404}
        
        image_bytes = self.bot.download_file(file_path)
        if not image_bytes:
            self.bot.send_message(chat_id, "something went wrong during file downloading")
            return{"message":"Not able to download image", "status_code":500}
        
        photo_buffer = self.resizer.image_resizer(image_bytes, resized_mb)
        resp =self.bot.send_photo(chat_id, photo_buffer, caption = f"Here is your resized image!of{resized_mb} mb" )

        if resp.get("status_code") not in [200, 201, 202, 203, 204]:
            self.bot.send_message(chat_id, "something went wrong while sending resized image")
            return{"message":"photo sending failed", "status_code": 500}
        
        print("processing complete succesfully")
        return{"message":"success", "status_code": 200}
    
def lambda_handler(event, context):
    token = os.environ.get("BOT_TOKEN")
    bot = TelegramBot(token)
    resizer = ImageResizer()
    handler= WebhookHandler(bot, resizer)
    
    return handler.process_event(event)


if __name__ == "__main__":
    try:
        with open("src/variables.json", "r") as f:
            token_data = json.load(f)
            os.environ["BOT_TOKEN"] = token_data.get("token", "")
    except Exception as e:
        print(f"Error found as ")

    try:
        with open("src/sample_event.json", "r") as f:
            sample_event= json.load(f)
        return_result = lambda_handler(sample_event, None)
        print(f"returned_result:{return_result}")
    except Exception as e:
        print(f"Error found as {e}")    



             







    

        
        








































