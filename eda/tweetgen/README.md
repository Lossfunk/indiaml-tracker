# Decoupled Tweet Generator

This document describes the refactored tweet generator that separates the HTML template from the Python code and accepts configuration via CLI arguments.

## Changes Made

### 1. Template Separation
- **Before**: HTML template was embedded as a string in `tweet_generator.py`
- **After**: HTML template is now in `templates/card_template.html`
- **Benefits**: 
  - Easy to modify template without touching Python code
  - Better separation of concerns
  - Template can be version controlled separately
  - Multiple templates can be used

### 2. CLI Arguments for Customization
The script now accepts several CLI arguments for customization:

#### Template and Branding
- `--template`: Path to custom HTML template file
- `--brand-text`: Brand text to display on cards (default: "India@ML")

#### Content Overrides
- `--conference`: Override conference name for all papers
- `--presentation-type`: Override presentation type for all papers

#### Existing Arguments
- `--format`: Output image format (png, jpg, jpeg, webp)
- `--output`: Output directory
- `--pdf`: Create merged PDF
- `--find-twitter`: Find Twitter handles
- `--find-twitter-only`: Only find Twitter handles
- `--max-concurrent`: Max concurrent Twitter searches

## Usage Examples

### Basic Usage
```bash
python tweet_generator.py input.json
```

### Custom Branding
```bash
python tweet_generator.py input.json --brand-text "NeurIPS 2025"
```

### Override Conference Info
```bash
python tweet_generator.py input.json --conference "ICLR 2025" --presentation-type "Poster"
```

### Custom Template
```bash
python tweet_generator.py input.json --template /path/to/custom_template.html
```

### Complete Example
```bash
python tweet_generator.py papers.json \
  --format png \
  --output cards/ \
  --brand-text "My Conference" \
  --conference "ICML 2025" \
  --presentation-type "Oral" \
  --pdf
```

## Template Structure

The HTML template uses Jinja2 syntax and expects these variables:

### Required Variables
- `paper.title`: Paper title
- `paper.conference`: Conference name
- `paper.presentation_type`: Presentation type
- `authors_to_display`: List of authors to show
- `remaining_authors`: Number of additional authors
- `logo_base64`: Base64 encoded logo
- `title_font_size`: Calculated font size
- `brand_text`: Brand text to display

### Template Location
- Default: `templates/card_template.html`
- Custom: Specify with `--template` argument

## Benefits of Decoupling

1. **Maintainability**: Template changes don't require Python code modifications
2. **Flexibility**: Easy to create different templates for different conferences
3. **Customization**: CLI arguments allow runtime customization without code changes
4. **Reusability**: Templates can be shared and reused across projects
5. **Version Control**: Templates can be tracked separately from code

## Migration from Old Version

If you were using the old embedded template version:

1. **No code changes needed** - the script maintains backward compatibility
2. **Template customization** - move your template modifications to `templates/card_template.html`
3. **Configuration** - use CLI arguments instead of hardcoded values

## Template Development

To create a custom template:

1. Copy `templates/card_template.html` to a new file
2. Modify the HTML/CSS as needed
3. Ensure all required Jinja2 variables are used
4. Test with `--template path/to/your/template.html`

The template system uses Jinja2, so you can use:
- Variables: `{{ variable_name }}`
- Conditionals: `{% if condition %}...{% endif %}`
- Loops: `{% for item in list %}...{% endfor %}`
- Filters: `{{ variable|filter_name }}`
