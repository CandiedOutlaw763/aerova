import json
from .ota_parsers import GenericParser

class IndiGoParser(GenericParser):
    def extract_lowest_price(self):
        # IndiGo DOMs sometimes load prices via JS variables or initial state.
        # Check script tags for JSON data
        scripts = self.soup.find_all("script")
        for s in scripts:
            if s.string and 'flightData' in s.string:
                # Add complex JSON parsing logic if needed
                pass
        return super().extract_lowest_price()

class AirIndiaParser(GenericParser):
    pass

class AirIndiaExpressParser(GenericParser):
    pass

class AkasaAirParser(GenericParser):
    pass

class SpiceJetParser(GenericParser):
    pass

def get_airline_parser(platform_name, html):
    parsers = {
        "IndiGo": IndiGoParser,
        "AirIndia": AirIndiaParser,
        "AirIndiaExpress": AirIndiaExpressParser,
        "AkasaAir": AkasaAirParser,
        "SpiceJet": SpiceJetParser
    }
    return parsers.get(platform_name, GenericParser)(html)
