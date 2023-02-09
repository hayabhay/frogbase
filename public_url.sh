# please get your own token from ngrok website: https://dashboard.ngrok.com/get-started/your-authtoken

ngrok config add-authtoken YOUR_NGROK_TOKEN
ngrok http 8501 > /dev/null &