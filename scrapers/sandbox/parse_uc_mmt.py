from bs4 import BeautifulSoup

html = open('uc_mmt_html.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

text = soup.get_text(separator=' ')
with open('uc_mmt_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved text to uc_mmt_text.txt")
