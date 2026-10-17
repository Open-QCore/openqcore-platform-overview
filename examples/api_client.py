
"""
Illustrative API client for an OpenAI-compatible chat endpoint.

Configure the endpoint and credentials using environment variables.
This example does not imply that a public OpenQCore API endpoint is available.
"""

import os
import sys

import requests


def main() -> None:
    base_url = os.getenv("OPENQCORE_API_BASE_URL", "").rstrip("/")
    api_key = os.getenv("OPENQCORE_API_KEY", "")
    model = os.getenv("OPENQCORE_MODEL", "example-model")

    if not base_url or not api_key:
        sys.exit(
            "Set OPENQCORE_API_BASE_URL and OPENQCORE_API_KEY "
            "before running this example."
        )

    endpoint = f"{base_url}/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Explain retrieval-augmented generation in 3 sentences.",
            }
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=(5, 45),
        )
        response.raise_for_status()
        result = response.json()

        answer = result["choices"][0]["message"]["content"]
        print(answer)

    except requests.RequestException as exc:
        sys.exit(f"API request failed: {exc}")
    except (KeyError, IndexError, ValueError):
        sys.exit("The API returned an unexpected response format.")


if __name__ == "__main__":
    main()
