# countgd-cli

A lightweight client for the [CountGD HF Space](https://huggingface.co/spaces/nikigoli/countgd) app to experiment with UI to support batch processing of images and videos and export in additional formats.

## Pre-requisites

- Python3.10+

## Installation
```bash
python3 -m venv env
source env/bin/activate

pip install .
```

## Usage

```bash
countgd run
```

### Using Docker
To make sure bind mounts work properly, we need to map the UID / GID within the container properly. To help with that run the following command
```bash
HOST_UID=$(id -u $USER) HOST_GID=$(id -g $USER) envsubst < .env.template > .env
```

Then, you can use the app within docker by
```bash
docker compose run --rm -it countgd-cli -- countgd --help
```

## Dev

TODO
- [x] Gradio interface to accept files
- [x] Show Image Prompter interface and let the user select an image as an upload
- [x] Make API call and display result one at a time.
- [x] Write to JSON
- [ ] Visualiser to overlay json on zip file

## Contributing
