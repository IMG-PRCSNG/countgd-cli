import logging
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()
app_state = {"verbose": True}
logger = logging.getLogger()


@app.callback()
def base(verbose: bool = False):
    """
    WISE CLI
    Search through collections of images with Text / Image
    """
    app_state["verbose"] = verbose
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s (%(threadName)s): %(name)s - %(levelname)s - %(message)s",
    )
    global logger
    logger = logging.getLogger()


@app.command()
def run():
    import gradio as gr

    from countgd_cli.interface import app

    with gr.Blocks(
        analytics_enabled=False,
        title="countgd-client",
        mode="app",
        fill_height=True,
        fill_width=True,
        css=".flex-1 { flex: 1 }",
    ) as blocks:
        app(blocks)

    blocks.queue().launch(debug=True)


@app.command()
def dummy(
    input_arg: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            file_okay=True,
            dir_okay=True,
            help="File / Directory with images to count objects from",
        ),
    ],
    count: Annotated[
        str, typer.Option(help="Text prompt representing the object to count")
    ],
):
    import gradio as gr
    from gradio_client import Client, handle_file

    client = Client("nikigoli/countgd")
    print(client.view_api())

    def count(image, text, prompts=None):
        if prompts is None:
            prompts = {"image": image, "points": []}

        result = client.predict(
            image=handle_file("strawberry.jpg"),
            text="strawberry",
            prompts=None,
            api_name="/count",
        )
        return result

    demo = gr.Interface(
        count,
        inputs=None,
        outputs=["image", "text"],
        title="CountGD",
        description="Count objects in the image using the Multimodal Open World Model",
    )
    demo.launch()
    logger.info("Calling Predict")
    pass


if __name__ == "__main__":
    app()
