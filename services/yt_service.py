from services.youtube_handler import YouTubeExtractor

extractor = YouTubeExtractor()

def get_video_info(url, extract_audio=False, quality="best"):
    return extractor.extract_video_info(url, extract_audio, quality)

def get_playlist_info(url, max_videos=20):
    return extractor.extract_playlist_info(url, max_videos)

def search(query, max_results=10):
    return extractor.search_videos(query, max_results)

def channel_videos(channel_url, max_videos=20):
    return extractor.get_channel_videos(channel_url, max_videos)

def stream_url(video_id, quality="best"):
    return extractor.get_video_stream_url(video_id, quality)