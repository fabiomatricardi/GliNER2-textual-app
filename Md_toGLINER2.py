#----------------------------------------------
# Load existig markdown file
#----------------------------------------------
# --------------------------------------------
# Use GliNER2 to extract bae documents data
# --------------------------------------------
import os
import json
from pathlib import Path
from docling.document_converter import DocumentConverter
import gradio as gr
from gliner2 import GLiNER2
from rich.console import Console
console = Console(width=90)
from datetime import datetime
from easygui import fileopenbox
from time import sleep
md = fileopenbox(msg='Pick your markdown', default='*.md')
with open(md, 'r', encoding='utf-8') as f:
    data = f.read()

# LOAD THE GLINER2 MODEL
with console.status("Loading the Gliner model..."):
    start = datetime.now()
    # Load the model
    extractor = GLiNER2.from_pretrained("gliner2-base-v1")
    console.print(f"Loaded in {datetime.now()-start}")
# CONVERSION
start = datetime.now()
mydata = data[:9900]
scheme = {
        "document_info": [
            "document number::str::Company Document ID",
            "document title::str::Title",
            "date::str::Last revision issue date",
            "project name::str::Project",
            "revision number::str::Last revision number"
        ]
    }
result = extractor.extract_json(
     mydata,scheme)
delta = datetime.now() - start
console.print(result)
console.print(f"Exectued in {delta}")