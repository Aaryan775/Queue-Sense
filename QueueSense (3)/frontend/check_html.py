import re

def check_html_structure(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple tag counters (avoiding self-closing tags)
    opening_divs = len(re.findall(r'<div\b', content))
    closing_divs = len(re.findall(r'</div>', content))
    
    opening_sections = len(re.findall(r'<section\b', content))
    closing_sections = len(re.findall(r'</section>', content))
    
    opening_main = len(re.findall(r'<main\b', content))
    closing_main = len(re.findall(r'</main>', content))

    print(f"Divs: Opens={opening_divs}, Closes={closing_divs}")
    print(f"Sections: Opens={opening_sections}, Closes={closing_sections}")
    print(f"Main: Opens={opening_main}, Closes={closing_main}")
    
    if opening_divs != closing_divs:
        print("WARNING: Mismatched DIV tags!")
    if opening_sections != closing_sections:
        print("WARNING: Mismatched SECTION tags!")

if __name__ == "__main__":
    check_html_structure("c:/Aneri/QueueSense/frontend/index.html")
