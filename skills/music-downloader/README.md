# music-downloader

🎵 Search and download audio from YouTube and other platforms with a single command.

## Features

| Feature | Description |
|---------|-------------|
| Search | `ytsearch<N>:Artist - Song` queries, no URL needed |
| Direct URLs | Any yt-dlp supported site (YouTube, SoundCloud, ...) |
| Formats | m4a (AAC), opus, mp3, flac |
| Metadata | `--add-metadata` + `--embed-thumbnail` for tags and album art |

## Format Reference

| Format ID | Codec | Quality | Extension |
|-----------|-------|---------|-----------|
| 251 | Opus | 133k | webm |
| 140 | AAC | 130k | m4a |
| 139 | AAC | 49k | m4a |

Use `251` for highest quality, `140` for best compatibility.

## Installation

```bash
npx skills add https://github.com/pipi32167/million-skills --skill music-downloader
```

## Requirements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (`pip install -U yt-dlp` if you hit HTTP 403 / SABR errors)
- ffmpeg (for extraction and format conversion)

## Usage

Ask for music in plain language:

- "download the song Bohemian Rhapsody"
- "get the mp3 of this video: https://..."
- "extract audio from this link as flac"
- "grab music with album art"

Example:

```bash
yt-dlp -f 140 -x --audio-format m4a \
  --add-metadata --embed-thumbnail \
  -o "%(title)s.%(ext)s" "ytsearch1:Artist - Song Name"
```

## Troubleshooting

- **HTTP 403 / SABR streams** — update yt-dlp to the latest version.
- **PO Token required** — use `--extractor-args "youtube:po_token=mweb.gvs+XXX"`.
- **Only images available** — try `--extractor-args "youtube:player_client=android"`.
