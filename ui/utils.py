from datetime import datetime
from pathlib import Path

import humanize


def get_formatted_date(date_str: str) -> str:
    """Converts an ISO formatted date string to a human readable format.

    Args:
        date_str: An ISO formatted date string.
    """
    # First convert to datetime object
    datetime_obj = datetime.fromisoformat(date_str)

    # Then convert to human readable format
    date = datetime_obj.strftime("%d %b %Y")
    time = datetime_obj.strftime("%I:%M%p")

    # Return formatted date
    return f"{time}, {date}"


def get_formatted_media_info(media_obj, details: bool = False) -> str:
    """Get a human readable string for the media object."""
    # Get the uploaded by string
    uploaded_by = media_obj.uploader_name if media_obj.uploader_name else media_obj.uploader_id
    if media_obj.uploader_url:
        uploaded_by_str = f'<a href="{media_obj.uploader_url}">{uploaded_by}</a>'
    else:
        uploaded_by_str = f"`{uploaded_by}`"

    # Get the uploaded date string
    uploaded_datestr = datetime.strptime(media_obj.upload_date, "%Y%m%d").strftime("%d %b %Y")

    # Get the original source string
    if media_obj.src.startswith("http"):
        original_str = f"<a href='{media_obj.src}'>{media_obj.src_name}</a>"
    else:
        original_str = media_obj.src_name

    infostr = ""
    if details:
        infostr += f""" <i>Title</i>: `{media_obj.title}`<br/>"""

    infostr += f"""
        <i>Source</i>: <b>{uploaded_by_str}</b> from <b>{original_str} `[{uploaded_datestr}]`</b><br/>
        <i>Added</i>: <b>`{get_formatted_date(media_obj.created)}`</b><br/>
        <i>Duration</i>: <b>`{int(float(media_obj.duration))}s`</b>; &nbsp; <i>Size</i>: <b>`{humanize.naturalsize(media_obj.filesize)}`</b><br/>
    """

    if details:
        infostr += f"""<i>Location</i>: `{media_obj.loc}`<br/>"""
        if media_obj.tags:
            infostr += f"""<i>Tags</i>: `{", ".join(media_obj.tags)}`<br/>"""
        if media_obj.description:
            infostr += f"""<hr/><b>Description</b>: {media_obj.description}<br/>"""

    return infostr
