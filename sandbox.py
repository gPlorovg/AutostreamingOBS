import os
import subprocess


for i in range(5):
    # is_online = os.system("ping -n 1 " + "google.com") == 0
    is_online = subprocess.call("ping -n 1 " + "google.com", shell=True) == 0
    print("new")
    print(is_online)
