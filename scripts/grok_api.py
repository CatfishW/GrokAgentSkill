#!/usr/bin/env python3
"""
Grok API CLI helper script.

Usage:
    python grok_api.py chat "Your message here" [--model MODEL] [--stream] [--key KEY]
    python grok_api.py file messages.json [--model MODEL] [--stream]
    python grok_api.py image "A red apple on a wooden table"
    python grok_api.py video "A glowing figure rotating in the dark"
    python grok_api.py models
    python grok_api.py verify

Set GROK_API_KEY env var or pass --key to authenticate.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

BASE_URL = "https://mc.agaii.org/grok/v1"
DEFAULT_MODEL = "grok-3"


def get_key(args):
    key = getattr(args, "key", None) or os.environ.get("GROK_API_KEY", "")
    if not key:
        print(
            "ERROR: No API key. Set GROK_API_KEY env var or pass --key <key>",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def make_request(path, key, payload=None, stream=False):
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    if stream:
        return resp
    return json.loads(resp.read().decode())


def cmd_chat(args):
    key = get_key(args)
    messages = [{"role": "user", "content": args.message}]
    payload = {
        "model": args.model,
        "messages": messages,
        "stream": args.stream,
    }
    if args.stream:
        resp = make_request("/chat/completions", key, payload, stream=True)
        for line in resp:
            line = line.decode().strip()
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    print()
                    break
                try:
                    data = json.loads(chunk)
                    delta = data["choices"][0]["delta"].get("content", "")
                    print(delta, end="", flush=True)
                except json.JSONDecodeError:
                    pass
    else:
        result = make_request("/chat/completions", key, payload)
        print(result["choices"][0]["message"]["content"])


def cmd_file(args):
    key = get_key(args)
    with open(args.messages_file) as f:
        messages = json.load(f)
    payload = {
        "model": args.model,
        "messages": messages,
        "stream": args.stream,
    }
    if args.stream:
        resp = make_request("/chat/completions", key, payload, stream=True)
        for line in resp:
            line = line.decode().strip()
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    print()
                    break
                try:
                    data = json.loads(chunk)
                    delta = data["choices"][0]["delta"].get("content", "")
                    print(delta, end="", flush=True)
                except json.JSONDecodeError:
                    pass
    else:
        result = make_request("/chat/completions", key, payload)
        print(result["choices"][0]["message"]["content"])


def cmd_models(args):
    key = get_key(args)
    result = make_request("/models", key)
    for m in result.get("data", []):
        print(m["id"])


def cmd_verify(args):
    key = get_key(args)
    # Use /models as a lightweight auth check (works with user sk- keys)
    result = make_request("/models", key)
    models = [m["id"] for m in result.get("data", [])]
    print(f"OK — {len(models)} models available")
    for m in models:
        print(f"  {m}")


def cmd_image(args):
    key = get_key(args)
    payload = {
        "model": "grok-imagine-1.0",
        "messages": [{"role": "user", "content": args.prompt}],
    }
    result = make_request("/chat/completions", key, payload)
    content = result["choices"][0]["message"]["content"]
    match = re.search(r'src="([^"]+)"', content)
    if match:
        print("Image URL:", match.group(1))
    else:
        print(content)


def cmd_video(args):
    key = get_key(args)
    payload = {
        "model": "grok-imagine-1.0-video",
        "messages": [{"role": "user", "content": args.prompt}],
    }
    print("Generating video (this takes 20–90 seconds)...", file=sys.stderr)
    resp = make_request("/chat/completions", key, payload, stream=True)
    full = b""
    last_progress = ""
    for line in resp:
        full += line
        line_str = line.decode().strip()
        if "进度" in line_str:
            try:
                data = json.loads(line_str.removeprefix("data: "))
                content = data["choices"][0]["delta"].get("content", "")
                if content.strip() and content != last_progress:
                    last_progress = content.strip()
                    print(f"\r{last_progress}", end="", file=sys.stderr, flush=True)
            except Exception:
                pass
    print(file=sys.stderr)
    full_str = full.decode(errors="replace")
    # Extract video URL
    match = re.search(r'src=\\"(https://[^"\\]+\.mp4)\\"', full_str)
    if match:
        print("Video URL:", match.group(1))
    else:
        # Try unescaped variant
        match = re.search(r'src="(https://[^"]+\.mp4)"', full_str)
        if match:
            print("Video URL:", match.group(1))
        else:
            print("Could not extract video URL. Raw output:", file=sys.stderr)
            print(full_str[-500:], file=sys.stderr)
    # Extract preview image
    match_img = re.search(r'poster=\\"(https://[^"\\]+)\\"', full_str)
    if match_img:
        print("Preview URL:", match_img.group(1))


def main():
    parser = argparse.ArgumentParser(description="Grok API CLI")
    parser.add_argument("--key", help="API key (overrides GROK_API_KEY env var)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # chat
    p_chat = sub.add_parser("chat", help="Send a single user message")
    p_chat.add_argument("message", help="The message to send")
    p_chat.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})"
    )
    p_chat.add_argument("--stream", action="store_true", help="Stream the response")
    p_chat.set_defaults(func=cmd_chat)

    # file
    p_file = sub.add_parser("file", help="Send messages from a JSON file")
    p_file.add_argument("messages_file", help="Path to JSON file with messages array")
    p_file.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})"
    )
    p_file.add_argument("--stream", action="store_true", help="Stream the response")
    p_file.set_defaults(func=cmd_file)

    # models
    p_models = sub.add_parser("models", help="List available models")
    p_models.set_defaults(func=cmd_models)

    # verify
    p_verify = sub.add_parser("verify", help="Verify API key is valid")
    p_verify.set_defaults(func=cmd_verify)

    # image
    p_image = sub.add_parser("image", help="Generate an image from a text prompt")
    p_image.add_argument("prompt", help="Image description")
    p_image.set_defaults(func=cmd_image)

    # video
    p_video = sub.add_parser("video", help="Generate a video from a text prompt")
    p_video.add_argument("prompt", help="Video description")
    p_video.set_defaults(func=cmd_video)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
