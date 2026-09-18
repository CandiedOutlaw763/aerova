from bs4 import BeautifulSoup
import re

class GenericParser:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, "html.parser")
        
    def extract_lowest_price(self):
        price_pattern = re.compile(r'(?:₹|Rs\.?)\s*([\d,]+)')
        texts = self.soup.find_all(string=price_pattern)
        
        prices = []
        for text in texts:
            match = price_pattern.search(text)
            if match:
                price_str = match.group(1).replace(",", "")
                if price_str.isdigit():
                    prices.append(int(price_str))
                    
        if prices:
            # Filter out suspiciously low prices (e.g. ₹99 seat selection fee)
            valid_prices = [p for p in prices if p > 1000]
            if valid_prices:
                return min(valid_prices)
        return None

class CleartripParser(GenericParser):
    def extract_lowest_price(self):
        # Specific CSS selector based on analysis
        elements = self.soup.find_all("p", class_="fOpaSt")
        prices = []
        for el in elements:
            text = el.get_text(strip=True)
            if '₹' in text:
                val = text.replace('₹', '').replace(',', '')
                if val.isdigit():
                    prices.append(int(val))
        
        if prices:
            return min(prices)
        return super().extract_lowest_price()

class EaseMyTripParser(GenericParser):
    def extract_lowest_price(self):
        # Specific CSS selector based on analysis
        elements = self.soup.find_all("div", class_="col-md-8 col-sm-8 col-xs-9 txt-r6-n ng-binding")
        prices = []
        for el in elements:
            text = el.get_text(strip=True)
            if text.isdigit():
                prices.append(int(text))
        
        # Fallback to general price class
        if not prices:
            elements = self.soup.find_all("span", class_="altrprice")
            for el in elements:
                text = el.get_text(strip=True).replace('from ₹', '').replace('→', '').replace(',', '').strip()
                if text.isdigit():
                    prices.append(int(text))
                    
        if prices:
            return min(prices)
        return super().extract_lowest_price()

class MakeMyTripParser(GenericParser):
    pass

class YatraParser(GenericParser):
    pass

class IxigoParser(GenericParser):
    pass

class GoibiboParser(GenericParser):
    pass

def get_ota_parser(platform_name, html):
    parsers = {
        "MakeMyTrip": MakeMyTripParser,
        "Yatra": YatraParser,
        "EaseMyTrip": EaseMyTripParser,
        "Cleartrip": CleartripParser,
        "Ixigo": IxigoParser,
        "Goibibo": GoibiboParser
    }
    return parsers.get(platform_name, GenericParser)(html)
