from bs4 import BeautifulSoup

with open('mmt_debug.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

inputs = soup.find_all('input')
for i in inputs:
    print(f"ID: {i.get('id')} | Class: {i.get('class')} | Placeholder: {i.get('placeholder')} | Type: {i.get('type')}")
