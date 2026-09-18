import re

html = open('uc_mmt_html.html', encoding='utf-8').read()
base_fares = re.findall(r'base[Ff]are["\']?\s*[:=]\s*\d+', html)
total_taxes = re.findall(r'total[Tt]ax(?:es)?["\']?\s*[:=]\s*\d+', html)
taxes = re.findall(r'tax(?:es)?["\']?\s*[:=]\s*\d+', html)
fees = re.findall(r'fee["\']?\s*[:=]\s*\d+', html)
udf = re.findall(r'udf["\']?\s*[:=]\s*\d+', html)

print(f"Base Fares: {len(base_fares)}")
if base_fares:
    print(base_fares[:5])
    
print(f"Total Taxes: {len(total_taxes)}")
if total_taxes:
    print(total_taxes[:5])

print(f"Taxes: {len(taxes)}")
if taxes:
    print(taxes[:5])

print(f"Fees: {len(fees)}")
if fees:
    print(fees[:5])
    
print(f"UDF: {len(udf)}")
if udf:
    print(udf[:5])
