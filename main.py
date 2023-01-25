import typer
import heatmap_clips
from typing import Optional, Union

main = typer.Typer()

@main.command()
def clip_heatmap(
    video_url: str = typer.Option(
        ..., 
        help="YouTube video URL.",
        path_type=str,
    ), 
    clip_length: Optional[int] = typer.Option(
        None, 
        help="Maximum video clip length in seconds.",
        path_type=int,
    ), 
    align: Optional[str] = typer.Option(
        None, 
        help="Clip allignment within a heatmap, either left, center, or right.",
        path_type=Optional[str],
    ), 
    clip_count: Optional[int] = typer.Option(
        None, 
        help="Maximum number of video clips to make.",
        path_type=int,
    ), 
    most_intense: Optional[bool] = typer.Option(
        None, 
        help="Make video clips in order of intensity.",
        path_type=bool,
    )
):
    """Clip YouTube video heatmap."""

    align = heatmap_clips.ClipAlign[align] if align else None

    video = heatmap_clips.Video(video_url)
    video.download()
    video_heatmap = heatmap_clips.get_video_heatmap(video)

    heatmaps = []

    if clip_count and most_intense:
        heatmaps = video_heatmap.most_intense_heatmaps(
            merge=False,
            count=clip_count,
        )
        
    elif clip_count:
        heatmaps = video_heatmap.heatmaps[:clip_count]

    else:
        heatmaps = video_heatmap.heatmaps

    video.generate_heatmap_clips(
        heatmaps=heatmaps,
        align=align,
        length=clip_length,
    )


@main.command()
def clip_chapters(
    video_url: str = typer.Option(
        ..., 
        help="YouTube video URL.",
        path_type=str,
    ), 
    clip_length: Optional[int] = typer.Option(
        None, 
        help="Maximum video clip length in seconds.",
        path_type=int,
    ), 
    align: Optional[str] = typer.Option(
        None, 
        help="Clip allignment within a chapter, either Left, Center, or Right.",
        path_type=str,
    ), 
    clip_count: Optional[int] = typer.Option(
        None, 
        help="Maximum number of video clips to make.",
        path_type=int,
    ), 
    most_intense: Optional[bool] = typer.Option(
        None, 
        help="Make video clips in order of intensity.",
        path_type=bool,
    )
):
    """Clip YouTube video chapters."""

    align = heatmap_clips.ClipAlign[align] if align else None

    video = heatmap_clips.Video(video_url)
    video.download()
    video_heatmap = heatmap_clips.get_video_heatmap(video)

    chapters = []

    if clip_count and most_intense:
        chapters = video_heatmap.most_intense_chapters(
            merge=False,
            count=clip_count,
        )
        
    elif clip_count:
        chapters = video_heatmap.chapters[:clip_count]

    else:
        chapters = video_heatmap.chapters

    video.generate_chapter_clips(
        chapters=chapters,
        align=align,
        length=clip_length,
    )


if __name__ == "__main__":
    main()