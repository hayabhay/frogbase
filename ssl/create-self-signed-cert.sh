#!/bin/bash

#openssl genrsa 2048 > server.key
#openssl req -new -key server.key > server.csr
#openssl x509 -days 3650 -req -sha256 -signkey server.key < server.csr > server.crt
#openssl x509 -text < server.crt

# https://qiita.com/miyuki_samitani/items/b19aa5ac3b3c6e312bd5
# https://qiita.com/sanyamarseille/items/46fc6ff5a0aca12e1946

# https://www.karakaram.com/creating-self-signed-certificate/
openssl req -x509 -sha256 -nodes -days 3650 -newkey rsa:2048 -subj /CN=localhost -keyout server.key -out server.crt
