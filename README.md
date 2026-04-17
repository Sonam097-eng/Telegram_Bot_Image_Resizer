# Telegram_Bot_Image_Resizer
# Serverless Telegram Image Resizer Bot 🤖📸

An event-driven, serverless Telegram bot built on AWS that automatically downloads, resizes, and returns high-resolution images sent by users. This project demonstrates cloud-native architecture, handling multipart API requests, and managing state in a NoSQL database.

## 🏗️ Architecture & Tech Stack

* **Compute:** AWS Lambda (Python 3.12, x86_64)
* **API Routing:** Amazon API Gateway (HTTP API webhook integration)
* **Database:** Amazon DynamoDB (User interaction tracking)
* **Image Processing:** `Pillow` (Custom AWS Lambda Layer)
* **External API:** Telegram Bot API (`urllib3` for memory-efficient HTTP requests)

## ✨ Key Features

* **In-Memory Processing:** Downloads and processes images entirely in RAM using `io.BytesIO()`, bypassing slow disk I/O for lightning-fast execution.
* **Custom Lambda Layers:** Utilizes a pre-compiled Amazon Linux (`manylinux2014`) Lambda Layer to run the C++ backed `Pillow` library in a serverless environment.
* **Multipart Form-Data Handling:** Streams the resized image directly back to the Telegram API without requiring intermediate cloud storage (like S3).
* **State Tracking:** Automatically logs user interactions, first names, and total message counts in DynamoDB.

## 🚀 How It Works

1. A user sends a photo to the Telegram Bot.
2. Telegram fires a JSON webhook to an **AWS API Gateway** endpoint.
3. API Gateway triggers the **AWS Lambda** function.
4. The Lambda function:
   * Extracts the `file_id` and queries Telegram for the direct download path.
   * Downloads the raw image bytes into memory.
   * Resizes the image to a maximum of 500x500 pixels (maintaining aspect ratio).
   * Updates the user's profile and message count in **DynamoDB**.
   * Sends the resized image back to the user via an HTTP POST request.

## 🛠️ Setup & Deployment

### 1. Prerequisites
* An AWS Account.
* A Telegram Bot Token (obtained from [@BotFather](https://t.me/BotFather) on Telegram).

### 2. DynamoDB Setup
Create a DynamoDB table with the following specifications:
* **Table name:** `TelegramBotData`
* **Partition key:** `user_id` (Type: String)

### 3. AWS Lambda Configuration
* **Runtime:** Python 3.12 (Architecture: `x86_64`)
* **Timeout:** Set to **30 seconds** (Image processing requires more than the default 3 seconds).
* **Memory:** Set to **512 MB** (To handle unpacking high-res images).
* **Environment Variables:**
  * Key: `BOT_TOKEN` | Value: `Your_Telegram_Bot_Token_Here`
* **IAM Role Permissions:** Ensure your Lambda execution role has `dynamodb:UpdateItem` permissions for your specific table.

### 4. Custom Pillow Layer
Because AWS Lambda does not natively support Pillow, you must attach a custom layer. Run this command locally to generate the correct Linux binaries:

```bash
mkdir python
pip install --platform manylinux2014_x86_64 --target=python --implementation cp --python-version 3.12 --only-binary=:all: --upgrade Pillow
zip -r pillow_layer.zip python/