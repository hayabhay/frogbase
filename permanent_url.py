import requests
import os
import time

PERM_URL='https://your.url.com'
my_url=None
new_url=''

# you can check if the service is alive by: 
# curl http://localhost:4040/api/tunnels

def get_ngrok_url():
    response=requests.get("http://localhost:4040/api/tunnels")
    return response.json()['tunnels'][0]['public_url']

# forword the curent url to the permanet url
def renew_forward(url):
    requests.post(f"{PERM_URL}/?new_url={url}")

if __name__ == '__main__':
    while 1:
        # get the url if possible 
        try:
            new_url = get_ngrok_url()
        except:
            # open the host if ngrok is not started
            os.system("bash public_url.sh")
            time.sleep(1)
            new_url = get_ngrok_url()

        # if the url changed
        if (not my_url) | (my_url != new_url):
            # update url record
            my_url = new_url
            # forward the url to PERM_URL
            renew_forward(my_url)

        time.sleep(600)
