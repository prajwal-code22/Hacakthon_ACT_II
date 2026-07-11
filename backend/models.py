import os
import requests

headers = {
    "Authorization": f"Bearer {'fw_62LhUn9xkk2SmTdA7PTjk3'}"
}

r = requests.get(
    "https://api.fireworks.ai/inference/v1/models",
    headers=headers
)

print(r.status_code)
print(r.text)