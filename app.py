"""
Application to generate daily updated data for topics and subtopics using the
OpenAI API and publicly available crypto endpoints.

Overview
--------

This script reads a structured list of topics and their sub‑topics from a YAML
file (`topics.yaml` by default), fetches daily information for each entry and
produces a consolidated report.  For crypto specific data (e.g. Bitcoin
chart and block time) the program queries publicly accessible endpoints on
``blockchain.info``.  For news and more open‑ended questions it uses the
OpenAI Chat Completions API to generate up‑to‑date summaries in German.

The OpenAI API key is not stored directly in this repository.  Instead it
should be saved as a Base64‑encoded string in a file with the suffix
``.enc`` (the default file is ``api_key.enc``).  Base64 encoding offers
basic obfuscation without requiring external dependencies such as
``cryptography``.  To generate your own encoded key, run the following
command in a shell (replace ``YOUR_KEY`` with the actual key):

    echo -n "YOUR_KEY" | base64 > api_key.enc

When the script runs it decodes the contents of the ``.enc`` file back into
the original API key.

Prerequisites
-------------

* Python 3.9 or newer
* The ``requests`` package (for HTTP requests)
* The ``openai`` package if you wish to call the OpenAI API
* A Base64 encoded OpenAI API key stored in ``api_key.enc``
* A ``topics.yaml`` file describing the topics and their sub‑topics

Example ``topics.yaml``
----------------------

The default configuration file expects a YAML mapping from a top‑level topic
to a list of sub‑topics:

```yaml
Bitcoin:
  - Chart
  - News
  - Blocktime
IT:
  - ChatGPT news
Politik:
  - Entscheidungen DE / Abstimmungen
```

Running the application
----------------------

Execute the script from a terminal.  You can override the path to the
topics file and the encoded key file with command–line arguments:

```sh
python app.py --topics-file topics.yaml --key-file api_key.enc --output report.json
```

The output is written to the file specified by ``--output`` (JSON by
default).  Each topic and sub‑topic will have its own entry in the
resulting JSON structure.
"""

import argparse
import base64
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests  # type: ignore
import yaml  # PyYAML is part of this environment

try:
    import openai  # type: ignore
except ImportError:
    openai = None  # handle gracefully if openai is not installed


def decode_key_file(path: Path) -> str:
    """Decode a Base64‑encoded API key from a file.

    Args:
        path: Path to the ``.enc`` file containing Base64 encoded data.

    Returns:
        The decoded API key as a string.

    Raises:
        ValueError: If the file cannot be decoded.
    """
    raw = path.read_text().strip()
    try:
        decoded_bytes = base64.b64decode(raw)
        return decoded_bytes.decode("utf‑8")
    except Exception as exc:  # broad catch to surface decoding errors
        raise ValueError(f"Failed to decode API key from {path}: {exc}")


def load_topics(path: Path) -> Dict[str, List[str]]:
    """Load topic definitions from a YAML file.

    The YAML file must consist of a mapping from topic names to a list of
    sub‑topic strings.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A dictionary where each key is a top‑level topic and each value is a
        list of sub‑topics.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the structure is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Topics file {path} not found")
    with path.open("r", encoding="utf‑8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Topics YAML must define a mapping from topic to list")
    result: Dict[str, List[str]] = {}
    for topic, subtopics in data.items():
        if not isinstance(subtopics, list):
            raise ValueError(f"Subtopics for '{topic}' must be a list")
        # ensure all subtopics are strings
        result[topic] = [str(s).strip() for s in subtopics]
    return result


def fetch_bitcoin_chart(days: int = 30) -> List[Dict[str, Any]]:
    """Fetch Bitcoin market price data for the last ``days`` days.

    The data is sourced from blockchain.com which hosts public historical price
    charts.  The returned list contains dictionaries with UNIX timestamps
    (seconds since epoch) and values in USD.  If the remote endpoint cannot
    be reached, an empty list is returned.

    Args:
        days: Number of days of history to retrieve.

    Returns:
        A list of ``{'timestamp': int, 'price': float}`` dictionaries.
    """
    endpoint = (
        f"https://blockchain.info/charts/market-price?timespan={days}days&format=json"
    )
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f"Warning: failed to fetch Bitcoin chart data: {exc}")
        return []
    values = []
    for entry in data.get("values", []):
        ts = entry.get("x")  # timestamp in seconds
        price = entry.get("y")  # price in USD
        if ts is None or price is None:
            continue
        values.append({"timestamp": int(ts), "price": float(price)})
    return values


def fetch_bitcoin_blocktime() -> Optional[float]:
    """Fetch the current average Bitcoin block time in seconds.

    Uses the blockchain.com plaintext query API ``/q/interval``.  If the
    request fails, returns ``None``.

    Returns:
        The average block time (seconds) or ``None`` on error.
    """
    url = "https://blockchain.info/q/interval"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        # The API returns a simple number as plain text
        return float(resp.text.strip())
    except Exception as exc:
        print(f"Warning: failed to fetch block time: {exc}")
        return None


def query_chat_completion(api_key: str, prompt: str, *, model: str = "gpt-3.5-turbo", temperature: float = 0.5, max_tokens: int = 800) -> str:
    """Query the OpenAI Chat Completions API with the provided prompt.

    This helper wraps the OpenAI API call and gracefully degrades if the
    ``openai`` module is unavailable.  In such cases, it returns an
    explanatory string instead of raising an ImportError.

    Args:
        api_key: Your OpenAI secret API key.
        prompt: The prompt to send to the assistant (in German for this app).
        model: The model identifier (default ``gpt-3.5-turbo``).
        temperature: Sampling temperature for the output.
        max_tokens: Maximum number of tokens to generate in the response.

    Returns:
        The assistant's response text.
    """
    if openai is None:
        return (
            "[OpenAI module not installed – unable to fetch live news. "
            "Install the 'openai' package to enable this feature.]"
        )
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein sachlicher deutscher Nachrichtenassistent."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return f"[Fehler bei der OpenAI‑Abfrage: {exc}]"


def handle_bitcoin(subtopic: str, api_key: str) -> Any:
    """Handle Bitcoin sub‑topics.

    Depending on the requested sub‑topic, dispatches to the appropriate
    helper:

    * ``Chart``    – returns a list of timestamp/price pairs for the last 30 days
    * ``Blocktime`` – returns the current average block time in seconds
    * ``News``     – uses the OpenAI API to generate a summary of the latest
                     Bitcoin news in German

    Args:
        subtopic: Name of the sub‑topic.
        api_key: OpenAI API key for news queries.

    Returns:
        A Python object representing the requested information.  For charts
        this will be a list of records; for block time a float; for news a
        string.
    """
    normalized = subtopic.strip().lower()
    today_str = _dt.datetime.now(_dt.timezone.utc).date().isoformat()
    if normalized == "chart":
        return fetch_bitcoin_chart()
    elif normalized == "blocktime":
        return fetch_bitcoin_blocktime()
    elif normalized == "news":
        prompt = (
            f"Fasse die wichtigsten Nachrichten zum Thema Bitcoin zum heutigen Datum {today_str} "
            "in deutscher Sprache zusammen. Führe die Meldungen in kurzen Bulletpoints auf."
        )
        return query_chat_completion(api_key, prompt)
    else:
        return f"[Unbekannter Bitcoin‑Unterpunkt: {subtopic}]"


def handle_it(subtopic: str, api_key: str) -> Any:
    """Handle IT sub‑topics.

    Currently only "ChatGPT news" is supported.  It invokes the OpenAI
    API to generate a summary of the latest ChatGPT related news.  If more
    sub‑topics are added in ``topics.yaml`` they will fall back to a
    default handler explaining that the topic is not recognised.
    """
    normalized = subtopic.strip().lower()
    today_str = _dt.datetime.now(_dt.timezone.utc).date().isoformat()
    if normalized in ("chatgpt news", "chatgpt news", "chatgpt-news"):
        prompt = (
            f"Welche aktuellen Nachrichten (Stand {today_str}) gibt es rund um ChatGPT und die "
            "neuesten Entwicklungen bei OpenAI? Fasse die wichtigsten Punkte in deutscher Sprache "
            "in kurzen Bulletpoints zusammen."
        )
        return query_chat_completion(api_key, prompt)
    else:
        return f"[Unbekannter IT‑Unterpunkt: {subtopic}]"


def handle_politik(subtopic: str, api_key: str) -> Any:
    """Handle Politik sub‑topics.

    For "Entscheidungen DE / Abstimmungen" the function uses the OpenAI API to
    summarise recent decisions and votes from German politics.  The date is
    passed into the prompt to ensure the assistant refers to the current day.
    """
    normalized = subtopic.strip().lower()
    today_str = _dt.datetime.now(_dt.timezone.utc).date().isoformat()
    if normalized.startswith("entscheid") or normalized.startswith("abstimm"):
        prompt = (
            f"Welche aktuellen politischen Entscheidungen oder Abstimmungen wurden in Deutschland zum "
            f"heutigen Datum {today_str} getroffen? Bitte fasse die wichtigsten Punkte in deutscher Sprache "
            "in kurzen Bulletpoints zusammen."
        )
        return query_chat_completion(api_key, prompt)
    else:
        return f"[Unbekannter Politik‑Unterpunkt: {subtopic}]"


def process_topics(topics: Dict[str, List[str]], api_key: str) -> Dict[str, Dict[str, Any]]:
    """Iterate through topics and sub‑topics, fetching relevant data.

    Args:
        topics: Mapping of topic names to subtopic lists.
        api_key: OpenAI API key for news summarisation.

    Returns:
        A nested dictionary.  The first level keys are the topics, the second
        level keys are sub‑topics, and the values are the gathered data.
    """
    results: Dict[str, Dict[str, Any]] = {}
    for topic, subtopics in topics.items():
        topic_results: Dict[str, Any] = {}
        for subtopic in subtopics:
            if topic.strip().lower() == "bitcoin":
                topic_results[subtopic] = handle_bitcoin(subtopic, api_key)
            elif topic.strip().lower() == "it":
                topic_results[subtopic] = handle_it(subtopic, api_key)
            elif topic.strip().lower() == "politik":
                topic_results[subtopic] = handle_politik(subtopic, api_key)
            else:
                topic_results[subtopic] = f"[Unbekanntes Thema: {topic}]"
        results[topic] = topic_results
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily data for topics using OpenAI and public APIs.")
    parser.add_argument(
        "--topics-file",
        type=Path,
        default=Path("topics.yaml"),
        help="Path to YAML file describing topics and subtopics",
    )
    parser.add_argument(
        "--key-file",
        type=Path,
        default=Path("api_key.enc"),
        help="Path to Base64 encoded OpenAI API key",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("report.json"),
        help="Path to write the resulting report (JSON format)",
    )
    args = parser.parse_args()

    # Load configuration
    try:
        topics = load_topics(args.topics_file)
    except Exception as exc:
        raise SystemExit(f"Fehler beim Lesen der Topics-Datei: {exc}")

    try:
        api_key = decode_key_file(args.key_file)
    except Exception as exc:
        raise SystemExit(f"Fehler beim Entschlüsseln des API-Schlüssels: {exc}")

    # Process topics
    report = process_topics(topics, api_key)

    # Write JSON output
    try:
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf‑8")
        print(f"Bericht erfolgreich in {args.output} geschrieben.")
    except Exception as exc:
        raise SystemExit(f"Fehler beim Schreiben der Ausgabedatei: {exc}")


if __name__ == "__main__":
    main()