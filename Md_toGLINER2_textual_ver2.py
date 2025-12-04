# textual_gliner_app.py
import json
import sys
from datetime import datetime
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Suppress noisy logs
import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("gliner2").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, RichLog, Static, Footer

try:
    from easygui import fileopenbox
except ImportError:
    raise ImportError("Please install easygui: pip install easygui")

from gliner2 import GLiNER2
from rich.markdown import Markdown


class GlinerMarkdownApp(App):
    TITLE = "GliNER2 Structured Data Extractor"
    CSS = """
    Horizontal {
        height: 1fr;
    }

    Vertical {
        width: 1fr;
    }

    #left-panel {
        width: 45%;
        padding: 1;
    }

    #right-panel {
        width: 55%;
        padding: 1;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }

    RichLog {
        height: 1fr;
        border: solid green;
    }

    #json-result {
        height: 1fr;
        background: $surface;
        color: $text;
        overflow-y: auto;
        border: solid green;
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.markdown_content = ""
        self.file_path = None
        self.extractor = None

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Button("Load Markdown File", id="load-btn", variant="primary"),
                Button.warning("Extract Structured Data", id="extract-btn", disabled=True),
                Static(id="json-result", expand=True),
                Button.error("Exit the app", id="exit-btn"),
                id="left-panel",
            ),
            Vertical(
                RichLog(id="markdown-view", wrap=True, highlight=False, markup=True),
                id="right-panel",
            ),
        )
        yield Footer()

    def on_mount(self):
        self.query_one("#json-result", Static).update("[dim]No data extracted yet.[/dim]")

    @on(Button.Pressed, "#load-btn")
    def load_markdown_file(self):
        file_path = fileopenbox(
            msg="Select a Markdown file",
            title="Open Markdown File",
            filetypes=["*.md", "*.markdown", "*.*"]
        )

        if file_path:
            file_path = Path(file_path)
            if file_path.suffix.lower() in (".md", ".markdown"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.markdown_content = f.read()
                    self.file_path = file_path

                    # Render Markdown using Rich
                    md_render = Markdown(self.markdown_content)
                    markdown_view = self.query_one("#markdown-view", RichLog)
                    markdown_view.clear()
                    markdown_view.write(md_render)

                    self.query_one("#extract-btn", Button).disabled = False
                    self.notify(f"✅ Loaded: {file_path.name}")
                except Exception as e:
                    self.notify(f"❌ Error reading file: {e}", severity="error")
            else:
                self.notify("⚠️ Please select a .md file.", severity="warning")
        else:
            self.notify("File selection canceled.", severity="warning")

    @on(Button.Pressed, "#extract-btn")
    def start_extraction(self):
        if not self.markdown_content:
            self.notify("❌ No markdown content to process.", severity="warning")
            return
        self.notify("▶️ Starting extraction...", severity="info")  # ← Add this
        self.query_one("#json-result", Static).update("[dim]Loading GliNER2 model...[/dim]")
        self.run_worker(self._do_extraction, exclusive=True, thread=True)

    async def _do_extraction(self):
        try:
            if self.extractor is None:
                # Temporarily suppress ANY stdout/stderr (e.g., tqdm, warnings)
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    start_load = datetime.now()
                    self.extractor = GLiNER2.from_pretrained("gliner2-base-v1")
                    load_time = datetime.now() - start_load
                load_msg = f"[green]Model loaded in {load_time.total_seconds():.2f}s[/green]\n"
            else:
                load_msg = ""

            text_input = self.markdown_content[:9900]

            scheme = {
                "document_info": [
                    "document number::str::Company Document ID",
                    "document title::str::Title",
                    "date::str::Last revision issue date",
                    "project name::str::Project",
                    "revision number::str::Last revision number",
                ]
            }

            start_extract = datetime.now()
            result = self.extractor.extract_json(text_input, scheme)
            extract_time = datetime.now() - start_extract

            json_str = json.dumps(result, indent=2, ensure_ascii=False)
            summary = f"\n[bold green]Extraction completed in {extract_time.total_seconds():.2f}s[/bold green]"

            final_output = load_msg + "\n" + json_str + summary
            self.call_from_thread(
                self.query_one("#json-result", Static).update,
                final_output
            )
        except Exception as e:
            self.call_from_thread(
                self.query_one("#json-result", Static).update,
                f"[red]❌ Extraction failed:\n{str(e)}[/red]"
            )
    @on(Button.Pressed, "#exit-btn")
    def exit_app(self):
        self.exit()

    # In GlinerMarkdownApp
    BINDINGS = [("ctrl+d", "toggle_dark", "Toggle Dark Mode"), ("ctrl+e", "quit", "Quit")]

if __name__ == "__main__":
    # NO sys.stdout override — let Textual manage its own I/O
    app = GlinerMarkdownApp()
    app.run()