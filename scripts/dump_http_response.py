"""
Copyright (c) Cutleast

Script to perform an HTTP request and dump the response into a JSON file.

Example usage:
With your Nexus Mods API key being in an environment variable:
    uv run scripts/dump_http_response.py --url https://api.nexusmods.com/v1/games/skyrimspecialedition/mods/12125/files.json --header "apikey: %NM_API_KEY%"
"""

import argparse
import json
from pathlib import Path
from typing import Any

import cloudscraper as cs
import requests
from cutleast_core_lib.core.utilities.env_resolver import resolve
from dotenv import load_dotenv


def run(args: argparse.Namespace) -> None:
    url: str = args.url
    method: str = args.method.upper()
    out_file = Path(args.out_file or "response.json")
    scrape: bool = args.scrape
    print_content: bool = args.print_content

    # Parse custom headers
    headers: dict[str, str] = {}
    if args.header:
        for header in args.header:
            if ":" not in header:
                print(f"Invalid header format (expected 'Key: Value'): {header}")
                continue

            key, value = header.split(":", 1)
            headers[key.strip()] = resolve(value.strip())

    print(
        f"Sending {method} request to '{url}' with headers {headers} and {scrape = }..."
    )
    response: requests.Response
    if not scrape:
        response = requests.request(method, url, headers=headers)
    else:
        response = cs.CloudScraper().request(method, url, headers=headers)

    try:
        response_body: Any = response.json()
    except ValueError:
        # fallback to text
        response_body = response.text

    if print_content:
        print("Response:", response_body)

    data: dict[str, Any] = {
        "url": url,
        "method": method,
        "status_code": response.status_code,
        "response_body": response_body,
        "response_headers": dict(
            # sort headers alphabetically
            sorted(response.headers.items(), key=lambda i: i[0].upper())
        ),
    }

    with out_file.open("w", encoding="utf-8") as file:
        file.write(json.dumps(data, indent=4, ensure_ascii=False))

    print(f"Response written to '{out_file}'.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send an HTTP request and dump the response into a JSON file."
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Target URL to request.",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="GET",
        help="HTTP method to use (default: GET).",
    )
    parser.add_argument(
        "--out-file",
        type=str,
        help="Path to the output JSON file. Defaults to response.json.",
    )
    parser.add_argument(
        "--header",
        action="append",
        help=(
            "Custom header in the format 'Key: Value'. Can be used multiple times.\n"
            "May also contain environment variables in the format '%%VAR%%'."
        ),
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        default=False,
        help=(
            "Toggles whether to send the request with CloudScraper instead of the "
            "standard requests library. This may be necessary to get HTML content."
        ),
    )
    parser.add_argument(
        "--print-content",
        action="store_true",
        default=False,
        help="Toggles whether to print the response content.",
    )

    run(parser.parse_args())


if __name__ == "__main__":
    load_dotenv()
    main()
