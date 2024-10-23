from modules.script_callbacks import on_ui_tabs
from modules import scripts, shared
import gradio as gr
import os
import re

IMG_PATTERN = '<img\s+[^>]*?src="(.+?)"[^>]*?>|!\[.*?\]\((.+?)\)'

SERVER: str = None
EXTENSIONS: dict[str, str] = {}

extensions_folder: str = os.path.dirname(scripts.basedir())
extensions: list[str] = [
    os.path.join(extensions_folder, d) for d in os.listdir(extensions_folder)
]

for folder in extensions:
    if not os.path.isdir(folder):
        continue

    files = os.listdir(folder)
    for file in files:
        if os.path.isfile(file) and file.lower().startswith("readme"):
            EXTENSIONS[f"{os.path.basename(folder)}/{os.path.splitext(file)[0]}"] = (
                os.path.join(folder, file)
            )


def _preprocess(file: str, text: str) -> str:
    folder: str = os.path.dirname(file)

    for m in re.finditer(IMG_PATTERN, text):
        path: str = (m.group(1) or m.group(2)).strip()
        if path.startswith("http"):
            continue

        relative_path: str = (
            path[1:] if (path.startswith("\\") or path.startswith("/")) else path
        )
        absolute_path: str = os.path.abspath(os.path.join(folder, relative_path))

        text = text.replace(path, f"{SERVER}{absolute_path}")

    return text


def _parse_url():
    global SERVER
    if SERVER is None:
        server: str = shared.demo.server_name
        port: int = shared.demo.server_port
        SERVER = f"http://{server}:{port}/file="


def _show(name: str) -> str:
    _parse_url()

    if name == "None":
        return gr.update(value=None, visible=False)

    with open(
        EXTENSIONS[name], "r", encoding="utf-8-sig", errors="xmlcharrefreplace"
    ) as f:
        data = _preprocess(EXTENSIONS[name], f.read())
        return gr.update(value=data, visible=True)


def readme_ui():
    opts: list = ["None"] + list(EXTENSIONS.keys())

    with gr.Blocks() as README:
        selection = gr.Dropdown(
            info="Select an Extension to view its README.md file",
            show_label=False,
            choices=opts,
            value="None",
        )
        display = gr.Markdown(
            line_breaks=True,
            visible=False,
        )
        selection.select(fn=_show, inputs=[selection], outputs=[display])

    return [(README, "README", "sd-webui-readme")]


on_ui_tabs(readme_ui)
