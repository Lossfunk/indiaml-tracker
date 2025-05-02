# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "docling-core",
#     "mlx-vlm",
#     "pillow",
# ]
# ///
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image
from docling_core.types.doc import ImageRefMode
from docling_core.types.doc.document import DocTagsDocument, DoclingDocument
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config, stream_generate

## Settings
SHOW_IN_BROWSER = True  # Export output as HTML and open in webbrowser.

## Load the model
model_path = "ds4sd/SmolDocling-256M-preview-mlx-bf16"
model, processor = load(model_path)
config = load_config(model_path)

## Prepare input
prompt = "Convert this page to docling."

# image = "https://ibm.biz/docling-page-with-list"
image = "https://ibm.biz/docling-page-with-table"

# Load image resource
if urlparse(image).scheme != "":  # it is a URL
    response = requests.get(image, stream=True, timeout=10)
    response.raise_for_status()
    pil_image = Image.open(BytesIO(response.content))
else:
    pil_image = Image.open(image)

# Apply chat template
formatted_prompt = apply_chat_template(processor, config, prompt, num_images=1)

## Generate output
print("DocTags: \n\n")

output = ""
for token in stream_generate(
    model, processor, formatted_prompt, [image], max_tokens=4096, verbose=False
):
    output += token.text
    print(token.text, end="")
    if "</doctag>" in token.text:
        break

print("\n\n")

# Populate document
doctags_doc = DocTagsDocument.from_doctags_and_image_pairs([output], [pil_image])
# create a docling document
doc = DoclingDocument(name="SampleDocument")
doc.load_from_doctags(doctags_doc)

## Export as any format
# Markdown
print("Markdown: \n\n")
print(doc.export_to_markdown())

# HTML
if SHOW_IN_BROWSER:
    import webbrowser

    out_path = Path("./output.html")
    doc.save_as_html(out_path, image_mode=ImageRefMode.EMBEDDED)
    webbrowser.open(f"file:///{str(out_path.resolve())}")
