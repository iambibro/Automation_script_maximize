import json
import re

def strip_html_tags(text):
    # Remove all HTML tags
    text = re.sub(r'<.*?>', '', text)
    return text

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
    output.append(f"{name}")
    output.append(f"{sku}")
    output.append(f"{denominations_str}")
    output.append(f"{description}\n")
    output.append("Update terms_and_conditions set terms =")
    output.append("'[")
    for idx, line in enumerate(tnc_lines):
        comma = ',' if idx < len(tnc_lines) - 1 else ''
        output.append(f'  "{line}"{comma}')
    output.append("]'")
    output.append("Where id = 0;\n")
    output.append("")
    output.append("Update terms_and_conditions set howToRedeem =")
    output.append("'[")
    for idx, line in enumerate(how_to_use_lines):
        comma = ',' if idx < len(how_to_use_lines) - 1 else ''
        output.append(f'  "{line}"{comma}')
    output.append("]'")
    output.append("Where id = 0;\n")
    return '\n'.join(output)

if __name__ == "__main__":
    with open('raw_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    result = extract_and_format(data)
    with open('result.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    print("Extraction complete! See result.txt for output.")
