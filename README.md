# WebPalette 🎨

Color Harvest is a Python tool that extracts and analyzes the color palette from any website. It helps designers, developers, and artists identify and use the exact colors from their favorite websites.

## Features

- 🌈 Extract the most common colors from any website
- 🖼️ Analyze colors from CSS, inline styles, and images
- ⚙️ Filter out grayscale, white, or black colors
- 📊 Generate a visual HTML palette for easy reference
- 💾 Export results to JSON for further processing
- 📋 One-click copy of hex values in the HTML output

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/color-harvest.git
cd color-harvest

# Install dependencies
pip install -r requirements.txt
```

### Requirements

- Python 3.6+
- BeautifulSoup4
- Requests
- Pillow

## Usage

### Basic Usage

```bash
python color_harvest.py https://example.com
```

This will:
1. Extract up to 20 most common colors from the website
2. Filter out grayscale, white, and black colors by default
3. Save results to a JSON file named after the domain
4. Generate an HTML visualization of the color palette

### Command Line Options

```bash
python color_harvest.py https://example.com [options]
```

| Option | Description |
|--------|-------------|
| `--colors N` | Number of colors to extract (default: 20) |
| `--output NAME` | Custom output filename base |
| `--keep-grayscale` | Include grayscale colors in results |
| `--keep-white` | Include white colors in results |
| `--keep-black` | Include black colors in results |
| `--keep-all` | Include all colors (no filtering) |

### Examples

Extract 30 colors from a website and include grayscale colors:
```bash
python color_harvest.py https://example.com --colors 30 --keep-grayscale
```

Save results with a custom filename:
```bash
python color_harvest.py https://example.com --output my_color_palette
```

Include all colors without filtering:
```bash
python color_harvest.py https://example.com --keep-all
```

## Output

### JSON Format

The tool creates a JSON file with the following structure:

```json
{
  "url": "https://example.com",
  "colors": [
    {"hex": "#3498db", "frequency": 42},
    {"hex": "#e74c3c", "frequency": 27},
    ...
  ],
  "filters": {
    "grayscale_filtered": true,
    "white_filtered": true,
    "black_filtered": true
  }
}
```

### HTML Visualization

The generated HTML file provides a visual representation of the color palette with:
- Color preview
- Hex value (clickable to copy)
- RGB value
- Occurrence count

## How It Works

Color Harvest analyzes websites through several methods:

1. Extracts colors from `<style>` tags in the HTML
2. Finds colors in inline style attributes
3. Downloads and analyzes linked CSS files
4. Processes images to identify dominant colors
5. Filters results based on user preferences
6. Generates a count of color occurrences
7. Creates an interactive HTML visualization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
