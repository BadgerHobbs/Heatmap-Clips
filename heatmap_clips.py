import json
import asyncio
import pyppeteer
import pydantic
import re
from typing import List, Optional, Union
import datetime
import yt_dlp
from moviepy.editor import *
import uuid
from enum import Enum

def milliseconds_to_time(milliseconds: int) -> datetime.time:
    """Convert milliseconds to datetime.time"""

    return datetime.time(
        int(milliseconds / 1000) // 3600, 
        (int(milliseconds / 1000) % 3600) // 60, 
        int(milliseconds / 1000) % 60
    )


def seconds_to_time(seconds: Union[int, float]) -> datetime.time:
    """Convert seconds to datetime.time"""

    if isinstance(seconds, float):
        seconds = int(round(seconds))

    return datetime.time(seconds // 3600, (seconds % 3600) // 60, seconds % 60)


def time_to_seconds(time: datetime.time) -> int:
    """Convert datetime.time to milliseconds"""

    return (time.hour * 60 + time.minute) * 60 + time.second


def valid_filename(filename: str):
    """Convert a string into a valid filename"""

    return re.sub(
        r'(?u)[^-\w.]', '', 
        str(filename).strip().replace(' ', '_')
    )


class Thumbnail(pydantic.BaseModel):
    """Data model for Thumbnail data"""

    url: str
    width: int
    height: int


class Chapter(pydantic.BaseModel):
    """Data model for Chapter data"""

    title: str
    start_time: datetime.time
    end_time: datetime.time
    thumbnails: List[Thumbnail]


class Heatmap(pydantic.BaseModel):
    """Data model for Heatmap data"""

    chapter: Optional[Chapter]
    start_time: Optional[datetime.time]
    end_time: Optional[datetime.time]
    intensity_score_normalised: Optional[float]


class VideoHeatmap(pydantic.BaseModel):
    """Data model for YouTube video Heatmap data"""

    url: str
    heatmaps: List[Heatmap]
        
    @property
    def chapters(self) -> List[Chapter]:
        """Get video chapters from heatmaps"""

        return [heatmap.chapter for heatmap in video_heatmap.heatmaps if heatmap.chapter]

    def most_intense_heatmaps(self, merge: bool=True, count: int=3) -> List[Heatmap]:
        """Return the most intense heatmaps, optionally joining by chapter title"""

        sorted_heatmaps = list(sorted(self.heatmaps, key=lambda x: x.intensity_score_normalised, reverse=True))

        if not merge or sum(1 for x in sorted_heatmaps if x.chapter) < count:
            return sorted_heatmaps[:count]

        merged_heatmaps = {}
        for heatmap in sorted_heatmaps:

            # Skip if heatmap has no chapter
            if not heatmap.chapter:
                continue

            # Add heatmap if not already exist and so far less than count added
            if not merged_heatmaps.get(heatmap.chapter.title) and len(merged_heatmaps) <= count:
                merged_heatmaps[heatmap.chapter.title] = heatmap

            else:
                merged_heatmap = merged_heatmaps.get(heatmap.chapter.title)

                if not merged_heatmap:
                    continue

                # Update heatmap times if different to existing
                if heatmap.start_time <= merged_heatmap.start_time:
                    merged_heatmap.start_time = heatmap.start_time
                
                if merged_heatmap.end_time <= heatmap.end_time:
                    merged_heatmap.end_time = heatmap.end_time

        return list(merged_heatmaps.values())


    def most_intense_chapters(self, merge: bool=True, count: int=3) -> List[Chapter]:
        """Return the most intense chapters"""

        return [heatmap.chapter for heatmap in self.most_intense_heatmaps(merge, count) if heatmap.chapter]


class ClipAlign(str, Enum):
    """Enumeration for clip allignment"""

    left = "left"
    center = "center"
    right = "right"


class Video:
    """Class to manage, download, and clip video"""

    url: str
    ydl_info: dict

    def __init__(self, url: str) -> None:
        self.url = url
        self.ydl_info = {}


    def download(self):
        """Download YouTube video using YT-Dlp"""

        ydl_opts = {
            "outtmpl": "/tmp/videos/%(id)s.%(ext)s",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.ydl_info = ydl.extract_info(self.url, download=True)


    def generate_clip(self, file_name: str, clip_file_name: str, start_time: datetime.time, end_time: datetime.time) -> None:
        """Generate clip using start time and end time, returning file name"""
                
        clip = VideoFileClip(f"tmp/videos/{file_name}").subclip(
            time_to_seconds(start_time) if time_to_seconds(start_time) > 0 else 0, 
            time_to_seconds(end_time) if time_to_seconds(end_time) < self.ydl_info["duration"] else None
        )
        
        """
        -vf: 
            This option is used to apply video filtergraph to the input video.
            In this case, the filtergraph is a series of filter commands that will be applied to the input video.
            The filtergraph is split into 3 parts:
            1. split [original][copy] : This filter command creates a copy of the input video and assigns it to the label "original" and "copy"
            2. [copy] crop=ih*9/16:ih:iw/2-ow/2:0, scale=1080:1920, gblur=sigma=50[blurred] : This filter command applies crop, scale and gblur to the video labeled as "copy"
            3. [original] scale=-1:1080, crop=1080:1080:iw/2-ow/2:ih/2-oh/2 [scaled]: This filter command applies scale and crop to the video labeled as "original"
            4. [blurred][scaled] overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2 : This filter command overlays the blurred video on top of the scaled video

        -auto-alt-ref:
            This option is used to enable use of alternate reference frames in VP9. It is used to improve the efficiency of the video compression.
            0 means it is disabled.

        -c:a:
            This option is used to set the codec for the audio stream.
            In this case, the audio stream is copied from the input file to the output file, without any changes.

        -c:v:
            This option is used to set the codec for the video stream.
            In this case, the codec for the video stream is set to h264.
        """
        ffmpeg_params = [
            "-vf", 
            "split [original][copy]; [copy] crop=ih*9/16:ih:iw/2-ow/2:0, scale=1080:1920, gblur=sigma=50[blurred]; [original] scale=-1:1080, crop=1080:1080:iw/2-ow/2:ih/2-oh/2 [scaled]; [blurred][scaled] overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2", 
            "-auto-alt-ref", "0", 
            "-c:a", "copy",
            "-c:v", "h264", 
        ]

        try:
            clip.write_videofile(
                f"tmp/clips/{clip_file_name}",
                preset="ultrafast",
                ffmpeg_params=ffmpeg_params,
            )
        except Exception as e:
            print(f"Error: {str(e)}")

        clip.close()


    def generate_chapter_clips(self, chapters: List[Chapter], align: Optional[ClipAlign]=ClipAlign.left, length: Optional[int]=None):
        """Generate clips from chapters"""

        for chapter in chapters:

            start_time = None
            end_time = None

            if length:

                if align == ClipAlign.left:
                    start_time = chapter.start_time
                    end_time = seconds_to_time(time_to_seconds(chapter.start_time) + length)

                elif align == ClipAlign.right:
                    start_time = seconds_to_time(time_to_seconds(chapter.start_time) - length)
                    end_time = chapter.end_time

                else:
                    middle = (time_to_seconds(chapter.start_time) + time_to_seconds(chapter.end_time)) // 2
                    start_time = seconds_to_time(middle - (length/2))
                    end_time = seconds_to_time(middle + (length/2))

            self.generate_clip(
                f"{self.ydl_info['id']}.webm", 
                f"{valid_filename(chapter.title)}.mp4",
                start_time or chapter.start_time,
                end_time or chapter.end_time,
            )


    def generate_heatmap_clips(self, heatmaps: List[Heatmap], align: Optional[ClipAlign]=ClipAlign.left, length: Optional[int]=None):
        """Generate clips from heatmaps"""

        for heatmap in heatmaps:

            start_time = None
            end_time = None

            if length:

                if align == ClipAlign.left:
                    start_time = heatmap.start_time
                    end_time = seconds_to_time(time_to_seconds(heatmap.start_time) + length)

                elif align == ClipAlign.right:
                    start_time = seconds_to_time(time_to_seconds(heatmap.start_time) - length)
                    end_time = heatmap.end_time

                else:
                    middle = (time_to_seconds(heatmap.start_time) + time_to_seconds(heatmap.end_time)) // 2
                    start_time = seconds_to_time(middle - (length/2))
                    end_time = seconds_to_time(middle + (length/2))

            self.generate_clip(
                f"{self.ydl_info['id']}.webm", 
                f"{heatmap.chapter.title if heatmap.chapter else uuid.uuid4()}.mp4",
                start_time or heatmap.start_time,
                end_time or heatmap.end_time,
            )


async def get_page_content(url: str) -> str:
    """Get page HTML content from URL"""

    # Create browser
    browser = await pyppeteer.launch()
    page = await browser.newPage()

    # Open video page and get HTML content
    await page.goto(url)
    html_content = await page.content()

    # Close page and browser
    await browser.close()

    return html_content


def get_initial_data(html_content: str) -> dict:
    """Get YouTube initial data from video URL"""

    # Get intitial video data
    yt_initial_data = re.search(
        r"var ytInitialData = (.*?);<",
        html_content,
        re.DOTALL,
    ).group(1)

    # Return YouTube intitial JSON data as dict
    return json.loads(yt_initial_data)


def get_marker_data(yt_initial_data: dict) -> dict:
    """Get YouTube marker data from intitial data"""

    return yt_initial_data["playerOverlays"]["playerOverlayRenderer"]["decoratedPlayerBarRenderer"]["decoratedPlayerBarRenderer"]["playerBar"]["multiMarkersPlayerBarRenderer"]["markersMap"]


def get_chapters(marker_data: dict, video: Video) -> List[Chapter]:
    """Get YouTube chapters from initial data"""

    chapter_data = []

    # Check if chapter data exists in marker data
    for data in marker_data:
        if data["key"] == "DESCRIPTION_CHAPTERS":
            chapter_data = [chapter["chapterRenderer"] for chapter in data["value"]["chapters"]]
            break

    chapters = []

    # Iterate over each chapter
    for i in range(0, len(chapter_data)):

        chapter = chapter_data[i]

        end_time = None
        if i+1 < len(chapter_data):
            end_time = milliseconds_to_time(chapter_data[i+1]["timeRangeStartMillis"])
        else:
            end_time = seconds_to_time(video.ydl_info["duration"])

        chapters.append(
            Chapter(
                title=chapter["title"]["simpleText"],
                start_time=milliseconds_to_time(chapter["timeRangeStartMillis"]),
                end_time=end_time,
                thumbnails=[Thumbnail(**thumbnail) for thumbnail in chapter["thumbnail"]["thumbnails"]],
            )
        )

    return chapters


def get_heatmaps(marker_data: dict, chapters: Optional[List[Chapter]]=[]) -> List[Heatmap]:
    """Get YouTube heatmap data from marker data"""

    heatmap_data = []

    # Check if chapter data exists in intital data
    for data in marker_data:
        if data["key"] == "HEATSEEKER":
            heatmap_data = [heatmap["heatMarkerRenderer"] for heatmap in data["value"]["heatmap"]["heatmapRenderer"]["heatMarkers"]]
            break

    heatmaps = []

    # Iterate over each heatmap
    for heatmap in heatmap_data:

        matching_chapter = None

        # Find a matching chapter timestamp if exists
        for chapter in chapters:

            if milliseconds_to_time(heatmap["timeRangeStartMillis"]) >= chapter.start_time:
                matching_chapter = chapter
    
        heatmaps.append(
            Heatmap(
                chapter=matching_chapter,
                start_time=milliseconds_to_time(heatmap["timeRangeStartMillis"]),
                end_time=milliseconds_to_time(heatmap["timeRangeStartMillis"] + heatmap["markerDurationMillis"]),
                intensity_score_normalised=heatmap["heatMarkerIntensityScoreNormalized"]
            )
        )

    return heatmaps


def get_video_heatmap(video: Video) -> VideoHeatmap:
    """Get YouTube video heatmap from URL"""

    event_loop = asyncio.get_event_loop()
    html_content = event_loop.run_until_complete(asyncio.gather(get_page_content(video.url)))[0]
    event_loop.close()

    initial_data = get_initial_data(html_content)
    marker_data = get_marker_data(initial_data)
    chapters = get_chapters(marker_data, video)
    heatmaps = get_heatmaps(marker_data, chapters)

    return VideoHeatmap(
        url=video.url,
        heatmaps=heatmaps,
    )
