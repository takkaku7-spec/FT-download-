from flask import Flask, request, jsonify
from pytubefix import YouTube
import re

app = Flask(__name__)


def get_video(url):
    if not url or not re.match(
        r"^https?://(www\.)?(youtube\.com|youtu\.be)/",
        url
    ):
        raise ValueError("Please enter a valid YouTube URL")

    return YouTube(url)


@app.route("/")
def home():
    return jsonify({
        "name": "FT YouTube Downloader API",
        "status": "Online",
        "endpoints": [
            "/video_info",
            "/available_resolutions",
            "/download/<resolution>"
        ]
    })


@app.route("/video_info", methods=["POST"])
def video_info():
    try:
        data = request.get_json(silent=True) or {}
        yt = get_video(data.get("url", "").strip())

        return jsonify({
            "title": yt.title,
            "author": yt.author,
            "views": yt.views,
            "duration": yt.length,
            "description": yt.description,
            "thumbnail": yt.thumbnail_url,
            "publish_date": str(yt.publish_date)
            if yt.publish_date else None
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/available_resolutions", methods=["POST"])
def resolutions():
    try:
        data = request.get_json(silent=True) or {}
        yt = get_video(data.get("url", "").strip())

        streams = yt.streams.filter(
            progressive=True,
            file_extension="mp4"
        )

        available = sorted(
            list({
                s.resolution for s in streams if s.resolution
            }),
            key=lambda x: int(x.replace("p", "")),
            reverse=True
        )

        return jsonify({"resolutions": available})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/download/<resolution>", methods=["POST"])
def download_video(resolution):
    try:
        if not re.fullmatch(r"\d{3,4}p", resolution):
            return jsonify({"error": "Invalid resolution"}), 400

        data = request.get_json(silent=True) or {}
        yt = get_video(data.get("url", "").strip())

        stream = yt.streams.filter(
            progressive=True,
            file_extension="mp4",
            resolution=resolution
        ).first()

        if not stream:
            return jsonify({
                "error": "Resolution not available"
            }), 404

        return jsonify({
            "title": yt.title,
            "resolution": stream.resolution,
            "download_url": stream.url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
