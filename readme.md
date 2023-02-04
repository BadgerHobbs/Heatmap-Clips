# Heatmap Clips
A command-line Python application which extracts, clips, and formats YouTube videos into short-form vertical videos.

- Typer is used for the command-line interfaces.
- Pyppeteer is used to extract the video metadata from YouTube (Chapters, heatmaps).
- Ytdlp is used to download the YouTube video.
- MoviePy and FFmpeg is used to clip, crop, blur, and render the vertical video clip.

## Features
- Automatically download YouTube video from URL, and generate clips.
- Generate clips based on heatmaps or chapters (if availible).
- Specify the specific length of clips.
- Specify the alignment of clips to chapters or heatmaps.
- Automatically crop image to 1080x1080, with blurred top and bottom margins.
- Generate any specified number of clips.

## Example
*Note: Low framerate due to being a .gif file*

![Animation-5](https://user-images.githubusercontent.com/23462440/216790959-53ffaef8-1078-4750-bb72-9638fcc84ccc.gif)

## Usage
The program uses Typer for the CLI, so you can use the below help commands to display the options availible.

```bash
main.py --help

 Usage: main.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                            │
│ --show-completion             Show completion for the current shell, to copy it or customize the   │
│                               installation.                                                        │
│ --help                        Show this message and exit.                                          │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────╮
│ clip-chapters                    Clip YouTube video chapters.                                      │
│ clip-heatmap                     Clip YouTube video heatmap.                                       │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```bash
main.py clip-heatmap --help

 Usage: main.py clip-heatmap [OPTIONS]

 Clip YouTube video heatmap.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --video-url                            TEXT     YouTube video URL. [default: None] [required]   │
│    --clip-length                          INTEGER  Maximum video clip length in seconds.           │
│                                                    [default: None]                                 │
│    --align                                TEXT     Clip allignment within a heatmap, either left,  │
│                                                    center, or right.                               │
│                                                    [default: None]                                 │
│    --clip-count                           INTEGER  Maximum number of video clips to make.          │
│                                                    [default: None]                                 │
│    --most-intense    --no-most-intense             Make video clips in order of intensity.         │
│                                                    [default: no-most-intense]                      │
│    --help                                          Show this message and exit.                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯

```


```bash
main.py clip-chapters --help

 Usage: main.py clip-chapters [OPTIONS]

 Clip YouTube video chapters.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --video-url                            TEXT     YouTube video URL. [default: None] [required]   │
│    --clip-length                          INTEGER  Maximum video clip length in seconds.           │
│                                                    [default: None]                                 │
│    --align                                TEXT     Clip allignment within a chapter, either Left,  │
│                                                    Center, or Right.                               │
│                                                    [default: None]                                 │
│    --clip-count                           INTEGER  Maximum number of video clips to make.          │
│                                                    [default: None]                                 │
│    --most-intense    --no-most-intense             Make video clips in order of intensity.         │
│                                                    [default: no-most-intense]                      │
│    --help                                          Show this message and exit.                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
