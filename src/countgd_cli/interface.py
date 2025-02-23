import json
import logging
from pathlib import Path

import gradio as gr
from gradio_client import Client, handle_file
from gradio_image_prompter import ImagePrompter
from httpx import Timeout

logger = logging.getLogger(__name__)


def make_count_request(client, image, text, prompts):
    if prompts is None:
        prompts = {"image": image, "points": []}

    heatmap, count = client.predict(
        image=handle_file(image),
        text=text,
        prompts={"image": handle_file(prompts["image"]), "points": prompts["points"]},
        api_name="/count_main",
    )
    return heatmap, count["value"]


def app(_blocks):
    def on_load():
        client = Client(
            "nikigoli/countgd", httpx_kwargs={"timeout": Timeout(10, connect=60)}
        )
        print(client.view_api())
        return client

    _countgd_client = gr.State(on_load)

    with gr.Column(visible=True) as input_column:
        with gr.Row(equal_height=True):
            text_prompt = gr.Textbox(
                label="What are we counting today?",
                placeholder="Description of the object you want to count",
                interactive=True,
            )
            with gr.Column(scale=0, min_width=120):
                count = gr.Button(
                    "Count",
                    variant="primary",
                    interactive=True,
                )
                clear = gr.ClearButton()
        with gr.Row(equal_height=True, elem_classes=["flex-1"]):
            # Add text box

            with gr.Column(scale=1):
                # Add gallery component to allow users to select image (or could it be filebrowser)
                gallery = gr.Gallery(
                    label="Input Image files",
                    value=None,
                    key="input",
                    scale=1,
                    height="100%",
                    interactive=True,
                    allow_preview=False,
                    type="filepath",
                )

            with gr.Column(scale=2):
                # Add Image prompter
                image_prompt = ImagePrompter(
                    type="filepath",
                    label="Exemplar",
                    value=None,
                    interactive=True,
                    visible=True,
                    scale=1,
                    height="100%",
                )

    with gr.Column(visible=False) as result_column:
        with gr.Row():
            count_output = gr.Markdown("**Counting...**")
            download_button = gr.DownloadButton("Download the file", visible=False)
            stop_button = gr.Button("Stop", variant="stop")
        progress_output = gr.Slider(interactive=False, label="Progress %")
        image_output = gr.Image(interactive=False, scale=1)

    # on run, switch to output mode
    def on_count(images, text, prompt):
        # check for images are present
        if len(images) == 0:
            raise gr.Error(
                "No images were provided - Please select images before counting!",
                duration=5,
            )

        # check for prompt
        if len(text) == 0 and prompt is None:
            raise gr.Error(
                "Please provide atleast one of (text prompt, visual prompt) to count!",
                duration=5,
            )

        # Start counting
        return {
            input_column: gr.Column(visible=False),
            result_column: gr.Column(visible=True),
            download_button: gr.DownloadButton(value=None, visible=False),
        }

    def on_start_count(images, text, prompt, client, req: gr.Request):
        print("Current Count: ", len(images), text, prompt)
        yield ("**Counting....**", None, 0, None)
        filename = Path(f"{req.session_hash}.json")
        count = -1
        heatmap = None

        counts = {}
        try:
            for idx, im in enumerate(images):
                # Start counting
                print("Counting", idx, im)
                count = -1
                heatmap = None
                image = im[0]
                try:
                    heatmap, count = make_count_request(client, image, text, prompt)
                except Exception:
                    logger.exception(f"Error getting prediction for {image}")
                finally:
                    image_hash = Path(image).parent.name
                    counts[image_hash] = {"name": Path(image).name, "count": count}
                    yield (
                        f"**Count: {count}**",
                        heatmap,
                        round(100.0 * (idx + 1) / len(images)),
                        None,
                    )
        finally:
            filename.write_text(json.dumps(counts, indent=2))
            yield (
                "**Completed**",
                heatmap,
                100,
                gr.DownloadButton(
                    visible=True, label="Download results", value=filename
                ),
            )

    count_event = count.click(
        on_count,
        inputs=[gallery, text_prompt, image_prompt],
        outputs={input_column, result_column, download_button},
        queue=False,
    ).success(
        on_start_count,
        inputs=[gallery, text_prompt, image_prompt, _countgd_client],
        outputs=[count_output, image_output, progress_output, download_button],
        show_progress="hidden",
    )

    def on_stop(val):
        print("Stopped")
        if val is not None and Path(Path(val).name).exists():
            print("delete file - ", val)
            Path(val).unlink(missing_ok=True)
        return {
            input_column: gr.Column(visible=True),
            result_column: gr.Column(visible=False),
        }

    stop_button.click(None, None, None, cancels=[count_event])
    stop_button.click(
        on_stop,
        inputs=[download_button],
        outputs={input_column, result_column},
        trigger_mode="multiple",
    )

    clear.add([text_prompt, gallery, image_prompt])

    def cleanup(req: gr.Request):
        filename = Path(f"{req.session_hash}.json")
        print("delete file - ", filename)
        Path(filename).unlink(missing_ok=True)

    blocks.unload(cleanup)


blocks = gr.Blocks(
    analytics_enabled=False,
    title="countgd-client",
    mode="app",
    fill_height=True,
    fill_width=True,
    css=".flex-1 { flex: 1 }",
)
if __name__ == "__main__":
    with blocks:
        app(blocks)

    blocks.queue().launch(debug=True)
