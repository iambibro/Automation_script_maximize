import json
import re

def strip_html_tags(text):
    # Remove all HTML tags
    return re.sub(r'<.*?>', '', text)

def extract_shortinfo(tnc_lines, how_to_use_lines):
    # Defaults
    where_to_redeem = "See T&C"
    single_or_multiple = "See T&C"
    clubbed = "See T&C"
    validity = "See T&C"

    # Where to Redeem
    # Enhanced Where to Redeem logic
    redeem_online = False
    redeem_store = False
    for line in tnc_lines + how_to_use_lines:
        l = line.lower()
        if "redeem" in l or "redemption" in l:
            if "online" in l or "website" in l or "app" in l:
                redeem_online = True
            if any(word in l for word in ["store", "outlet", "in-store", "counter"]):
                redeem_store = True

    if redeem_online and redeem_store:
        where_to_redeem = "Redeem online and at store counters"
    elif redeem_online:
        where_to_redeem = "Redeem online"
    elif redeem_store:
        where_to_redeem = "Redeem at store counters"
    else:
        where_to_redeem = "See T&C"

    # Single Use or Multiple Use
    for line in tnc_lines:
        if "cannot be redeemed partially" in line.lower():
            single_or_multiple = "Must use the full balance in one go"
            break
        elif "partial redemption" in line.lower() or "can be used multiple times" in line.lower():
            if "not" in line.lower() or "cannot" in line.lower():
                single_or_multiple = "Must use the full balance in one go"
            else:
                single_or_multiple = "Can be used multiple times until balance is zero"
            break

    # Can the cards be clubbed?
    for line in tnc_lines:
        m = re.search(r'maximum of (\d+) gift cards', line.lower())
        if m:
            clubbed = f"Use up to {m.group(1)} gift cards in one purchase."
            break
        elif "multiple gift cards" in line.lower() or "can be clubbed" in line.lower():
            clubbed = "Multiple gift cards can be used in one purchase."
            break

        # Validity
    # validity = "See T&C"
    for line in tnc_lines:
        # Look for patterns like 'valid for 12 months', 'valid for 1 year', etc.
        m = re.search(r'valid\s*(?:for|ity)?\s*(?:of)?\s*(\d+)\s*(year|month|years|months)', line.lower())
        if m:
            num = m.group(1)
            unit = m.group(2)
            # Normalize unit
            if unit.startswith('year'):
                unit_str = "year" if num == "1" else "years"
            else:
                unit_str = "month" if num == "1" else "months"
            validity = f"Valid for {num} {unit_str}"
            break
        # Try to catch cases like 'validity: 6 months'
        m2 = re.search(r'validity\s*[:\-]?\s*(\d+)\s*(year|month|years|months)', line.lower())
        if m2:
            num = m2.group(1)
            unit = m2.group(2)
            if unit.startswith('year'):
                unit_str = "year" if num == "1" else "years"
            else:
                unit_str = "month" if num == "1" else "months"
            validity = f"Valid for {num} {unit_str}"
            break

    # # Validity
    # for line in tnc_lines:
    #     m = re.search(r'valid\s*for\s*(\d+)\s*(year|month|months)', line.lower())
    #     if m:
    #         num = m.group(1)
    #         unit = m.group(2)
    #         if unit.startswith('month'):
    #             validity = f"Valid for {num} month only"
    #         else:
    #             validity = f"Valid for {num} year only"
    #         break
    #     elif "valid for" in line.lower():
    #         # fallback, just use the whole line
    #         validity = re.sub(r'\.$', '', line)
    #         break

    # Compose shortInfo
    shortinfo = [
        {
            "icon": " https://savemax.s3.ap-south-1.amazonaws.com/giftcard/icons/pay-online-offline-icon.svg",
            "title": "Where to Redeem?",
            "subtext": where_to_redeem
        },
        {
            "icon": " https://savemax.s3.ap-south-1.amazonaws.com/giftcard/icons/how-to-use-icon.svg",
            "title": "Single Use or Multiple Use?",
            "subtext": single_or_multiple
        },
        {
            "icon": " https://savemax.s3.ap-south-1.amazonaws.com/giftcard/icons/clubbale-icon.svg",
            "title": "Can the cards be clubbed?",
            "subtext": clubbed
        },
        {
            "icon": " https://savemax.s3.ap-south-1.amazonaws.com/giftcard/icons/calender-icon.svg",
            "title": "Validity",
            "subtext": validity
        }
    ]
    return shortinfo

def extract_and_format(json_data):
    name = json_data['data'].get('name', '')
    sku = json_data['data'].get('sku', '')
    denominations = json_data.get('price', {}).get('denominations', [])
    denominations_str = ','.join(str(d) for d in denominations)
    description = json_data['data'].get('description', '')

    # T&C content: split, strip HTML, clean
    tnc_content = json_data['data'].get('tnc', {}).get('content', '')
    tnc_lines = [
        strip_html_tags(line).strip().replace("'", '"')
        for line in re.split(r'<br\s*/?>|\n', tnc_content)
        if strip_html_tags(line).strip()
    ]

    # How to use: strip HTML, clean
    how_to_use_html = json_data['data'].get('cpg', {}).get('howToUse', '')
    how_to_use_lines = []
    if how_to_use_html:
        text = re.sub(r'</?p>', '\n', how_to_use_html)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'<.*?>', '', text)
        for line in text.split('\n'):
            clean = line.strip()
            if clean:
                clean = re.sub(r'^[•\-\*]\s*', '', clean)
                how_to_use_lines.append(clean.replace("'", '"'))

    # Prepare output
    output = []
    output.append(f"{name}\n")
    output.append(f"{sku}\n")
    output.append(f"{denominations_str}\n")
    output.append(f"{description}\n")
    output.append("")
    output.append("Update terms_and_conditions set terms = ")
    output.append("'[")
    for idx, line in enumerate(tnc_lines):
        comma = ',' if idx < len(tnc_lines) - 1 else ''
        output.append(f'  "{line}"{comma}')
    output.append("]'")
    output.append("Where id = 0;\n")
    output.append("")
    output.append("")
    output.append("Update terms_and_conditions set howToRedeem = ")
    output.append("'[")
    for idx, line in enumerate(how_to_use_lines):
        comma = ',' if idx < len(how_to_use_lines) - 1 else ''
        output.append(f'  "{line}"{comma}')
    output.append("]'")
    output.append("Where id = 0;\n")
    output.append("")
    output.append("")
    # Add shortInfo
    shortinfo = extract_shortinfo(tnc_lines, how_to_use_lines)
    output.append("Update gift_cards set shortInfo = ")
    output.append("'" + json.dumps(shortinfo, indent=2, ensure_ascii=False) + "' ")
    output.append("where id = 0;")
    return '\n'.join(output)

if __name__ == "__main__":
    with open('raw_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    result = extract_and_format(data)
    with open('result.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    print("Extraction complete! See result.txt for output.")
