import requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
}
response = requests.get('https://www.goindigo.in/', headers=headers)
with open('indigo_home.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("Downloaded homepage.")
