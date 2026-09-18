import json
from engine.spiders.indigo import Spider

def test_indigo():
    spider = Spider()
    spider.scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")

if __name__ == "__main__":
    test_indigo()
