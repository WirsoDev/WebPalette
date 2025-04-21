#!/Users/wilson/dev/WebPalette/venv/bin/python
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import json
import argparse
from urllib.parse import urlparse
import os
from PIL import Image
from io import BytesIO
import logging
import colorsys

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def normalize_hex_color(color):
    """Normalize hex color to 6-digit format with '#' prefix."""
    color = color.lower()
    if len(color) == 4:  # Transform #RGB to #RRGGBB
        r, g, b = color[1], color[2], color[3]
        return f"#{r}{r}{g}{g}{b}{b}"
    return color

def rgb_to_hex(rgb_match):
    """Convert RGB color to hex format."""
    r, g, b = map(int, rgb_match.groups())
    return f"#{r:02x}{g:02x}{b:02x}"

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = normalize_hex_color(hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

def is_grayscale(hex_color, threshold=10):
    """Check if a color is grayscale (including white and black)."""
    r, g, b = hex_to_rgb(hex_color)
    # Check if R, G, B values are close to each other
    return (abs(r - g) <= threshold and abs(g - b) <= threshold and abs(r - b) <= threshold)

def is_too_white(hex_color, threshold=240):
    """Check if a color is too close to white."""
    r, g, b = hex_to_rgb(hex_color)
    return (r >= threshold and g >= threshold and b >= threshold)

def is_too_black(hex_color, threshold=20):
    """Check if a color is too close to black."""
    r, g, b = hex_to_rgb(hex_color)
    return (r <= threshold and g <= threshold and b <= threshold)

def should_filter_color(hex_color, filter_grayscale=True, filter_white=True, filter_black=True):
    """Determine if a color should be filtered out."""
    if filter_white and is_too_white(hex_color):
        return True
    if filter_black and is_too_black(hex_color):
        return True
    if filter_grayscale and is_grayscale(hex_color):
        return True
    return False

def extract_colors_from_css(css_text):
    """Extract color values from CSS text."""
    colors = []
    
    # Extract hex colors
    hex_colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', css_text)
    colors.extend([normalize_hex_color(color) for color in hex_colors])
    
    # Extract rgb colors
    rgb_pattern = re.compile(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)')
    for match in rgb_pattern.finditer(css_text):
        colors.append(rgb_to_hex(match))
    
    # Extract rgba colors (convert to hex, ignoring alpha)
    rgba_pattern = re.compile(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d\.]+\)')
    for match in rgba_pattern.finditer(css_text):
        colors.append(rgb_to_hex(match))
    
    return colors

def extract_colors_from_image(img_url, base_url):
    """Extract dominant color from an image."""
    try:
        # Resolve relative URLs
        if not img_url.startswith(('http://', 'https://')):
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = base_url + img_url
            else:
                img_url = base_url + '/' + img_url
        
        response = requests.get(img_url, timeout=5)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            # Resize for faster processing
            img.thumbnail((100, 100))
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Simple algorithm to get dominant color
            colors = img.getcolors(maxcolors=1000)
            if colors:
                # Sort colors by count (most frequent first)
                colors.sort(reverse=True, key=lambda x: x[0])
                # Convert (r,g,b) to hex
                dominant_color = colors[0][1]
                return f"#{dominant_color[0]:02x}{dominant_color[1]:02x}{dominant_color[2]:02x}"
    except Exception as e:
        logging.debug(f"Failed to extract color from image {img_url}: {e}")
    return None

def get_clean_filename(url, extension=".json"):
    """Create a clean filename from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    # Remove non-alphanumeric characters
    domain = re.sub(r'[^a-zA-Z0-9]', '_', domain)
    return f"{domain}{extension}"

def get_display_name(url):
    """Get a display name from the URL."""
    parsed = urlparse(url)
    domain = parsed.netloc
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def get_text_color(bg_hex):
    """Determine appropriate text color (black or white) based on background color."""
    r, g, b = hex_to_rgb(bg_hex)
    # Calculate relative luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#ffffff" if luminance < 0.5 else "#000000"

def generate_html_page(url, colors_data, output_file):
    """Generate HTML visualization of the color palette."""
    site_name = get_display_name(url)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_name} - Color Harvest</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        body {{
            background-color: #f5f5f7;
            padding: 2rem;
        }}
        header {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        h1 {{
            font-size: 2.5rem;
            color: #333;
            margin-bottom: 0.5rem;
        }}
        .subtitle {{
            color: #666;
            font-size: 1.2rem;
        }}
        .color-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1.5rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .color-card {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .color-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
        }}
        .color-preview {{
            height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: bold;
        }}
        .color-info {{
            padding: 1rem;
            background-color: white;
        }}
        .color-hex {{
            font-family: monospace;
            font-size: 1.2rem;
            font-weight: bold;
            display: block;
            margin-bottom: 0.5rem;
            cursor: pointer;
            padding: 6px 10px;
            border-radius: 4px;
            background-color: #f0f0f0;
            transition: background-color 0.2s;
        }}
        .color-hex:hover {{
            background-color: #e0e0e0;
        }}
        .color-frequency {{
            font-size: 0.9rem;
            color: #666;
        }}
        .copy-message {{
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: #333;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }}
        .rgb-value {{
            font-family: monospace;
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
        }}
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            color: #666;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <header>
        <h1>WebPallet</h1>
        <div class="subtitle">Color palette for <a href="{url}" target="_blank">{site_name}</a></div>
    </header>

    <div class="color-grid">
"""
    
    # Add color cards
    for color in colors_data:
        hex_value = color["hex"]
        frequency = color["frequency"]
        text_color = get_text_color(hex_value)
        rgb = hex_to_rgb(hex_value)
        
        html_template += f"""
        <div class="color-card">
            <div class="color-preview" style="background-color: {hex_value}; color: {text_color};">
                {hex_value}
            </div>
            <div class="color-info">
                <div class="color-hex" onclick="copyToClipboard('{hex_value}')" title="Click to copy">
                    {hex_value}
                </div>
                <div class="rgb-value">
                    RGB({rgb[0]}, {rgb[1]}, {rgb[2]})
                </div>
                <div class="color-frequency">
                    {frequency} occurrence{'' if frequency == 1 else 's'}
                </div>
            </div>
        </div>
"""
    
    # Complete the HTML
    html_template += """
    </div>

    <div class="copy-message" id="copyMessage">Copied to clipboard!</div>

    <footer>
        <p>Generated with WebPalette</p>
    </footer>

    <script>
        function copyToClipboard(text) {
            // Create temporary element
            const el = document.createElement('textarea');
            el.value = text;
            document.body.appendChild(el);
            
            // Select and copy text
            el.select();
            document.execCommand('copy');
            
            // Remove temporary element
            document.body.removeChild(el);
            
            // Show message
            const message = document.getElementById('copyMessage');
            message.textContent = `${text} copied to clipboard!`;
            message.style.opacity = 1;
            
            // Hide message after 2 seconds
            setTimeout(() => {
                message.style.opacity = 0;
            }, 2000);
        }
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    logging.info(f"HTML palette visualization saved to {output_file}")

def extract_colors_from_website(url, max_colors=20, filter_grayscale=True, filter_white=True, filter_black=True):
    """Extract colors from a website and count their frequency."""
    logging.info(f"Extracting colors from {url}")
    
    # Get base URL for resolving relative paths
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logging.error(f"Failed to fetch website. Status code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching website: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    all_colors = []
    
    # Extract colors from style tags
    for style in soup.find_all('style'):
        all_colors.extend(extract_colors_from_css(style.text))
    
    # Extract colors from inline styles
    for tag in soup.find_all(style=True):
        all_colors.extend(extract_colors_from_css(tag['style']))
    
    # Extract colors from external CSS files
    for link in soup.find_all('link', rel='stylesheet'):
        if 'href' in link.attrs:
            css_url = link['href']
            try:
                # Resolve relative URLs
                if not css_url.startswith(('http://', 'https://')):
                    if css_url.startswith('//'):
                        css_url = 'https:' + css_url
                    elif css_url.startswith('/'):
                        css_url = base_url + css_url
                    else:
                        css_url = base_url + '/' + css_url
                
                css_response = requests.get(css_url, timeout=5)
                if css_response.status_code == 200:
                    all_colors.extend(extract_colors_from_css(css_response.text))
            except Exception as e:
                logging.debug(f"Failed to fetch CSS file {css_url}: {e}")
    
    # Extract colors from images (this can be time-consuming)
    for img in soup.find_all('img', src=True)[:10]:  # Limit to first 10 images
        color = extract_colors_from_image(img['src'], base_url)
        if color:
            all_colors.append(color)
    
    # Filter out grayscale, white, and black colors if requested
    filtered_colors = []
    for color in all_colors:
        if not should_filter_color(color, filter_grayscale, filter_white, filter_black):
            filtered_colors.append(color)
    
    # Count color frequencies
    color_counter = Counter(filtered_colors)
    
    # Get the most common colors
    most_common_colors = [
        {"hex": color, "frequency": count}
        for color, count in color_counter.most_common(max_colors)
    ]
    
    logging.info(f"Extracted {len(most_common_colors)} colors after filtering")
    return most_common_colors

def main():
    """Main entry point for the script."""
    setup_logging()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Color Harvest - Extract colors from a website')
    parser.add_argument('url', help='URL of the website to analyze')
    parser.add_argument('--colors', type=int, default=20, help='Number of colors to extract (default: 20)')
    parser.add_argument('--output', help='Custom output filename base (without extension)')
    parser.add_argument('--keep-grayscale', action='store_true', help='Include grayscale colors')
    parser.add_argument('--keep-white', action='store_true', help='Include white colors')
    parser.add_argument('--keep-black', action='store_true', help='Include black colors')
    parser.add_argument('--keep-all', action='store_true', help='Include all colors (no filtering)')
    args = parser.parse_args()
    
    url = args.url
    max_colors = args.colors
    
    # Determine filter settings
    filter_grayscale = not (args.keep_grayscale or args.keep_all)
    filter_white = not (args.keep_white or args.keep_all)
    filter_black = not (args.keep_black or args.keep_all)
    
    colors_data = extract_colors_from_website(
        url, 
        max_colors, 
        filter_grayscale=filter_grayscale,
        filter_white=filter_white,
        filter_black=filter_black
    )
    
    if not colors_data:
        logging.error("Failed to extract colors from the website.")
        return
    
    # Create output filenames
    if args.output:
        base_filename = args.output
        json_filename = f"{base_filename}.json"
        html_filename = f"{base_filename}.html"
    else:
        base_name = get_clean_filename(url, "")
        json_filename = f"{base_name}.json"
        html_filename = f"{base_name}.html"
    
    # Save results to JSON file
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "url": url, 
            "colors": colors_data,
            "filters": {
                "grayscale_filtered": filter_grayscale,
                "white_filtered": filter_white,
                "black_filtered": filter_black
            }
        }, f, indent=2)
    
    # Generate HTML visualization
    generate_html_page(url, colors_data, html_filename)
    
    logging.info(f"Results saved to {json_filename}")
    
    # Print summary
    print(f"\nColor Harvest Results for {url}")
    print("-" * 50)
    for i, color_data in enumerate(colors_data, 1):
        print(f"{i}. {color_data['hex']} - {color_data['frequency']} occurrences")
    print("-" * 50)
    print(f"Filters applied: Grayscale: {'Yes' if filter_grayscale else 'No'}, " +
          f"White: {'Yes' if filter_white else 'No'}, " +
          f"Black: {'Yes' if filter_black else 'No'}")
    print(f"Data saved to {json_filename}")
    print(f"Visual palette saved to {html_filename}")

if __name__ == "__main__":
    main()


