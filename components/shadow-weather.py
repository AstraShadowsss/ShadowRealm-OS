#!/usr/bin/env python3
"""Fetch the MET Norway forecast for a manually chosen location."""

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROVIDER = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
USER_AGENT = "ShadowRealm-OS Weather (https://github.com/AstraShadowsss/ShadowRealm-OS)"
RETRY_AFTER = timedelta(hours=3)


@dataclass(frozen=True)
class Forecast:
    valid_at: str
    temperature_c: float
    condition: str | None
    precipitation_mm: float | None


@dataclass(frozen=True)
class WeatherCache:
    location: tuple[str, str]
    forecast: Forecast
    refresh_at: datetime
    last_modified: str | None


def coordinates(latitude, longitude):
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Enter a latitude from -90 to 90 and longitude from -180 to 180.")
    return f"{latitude:.2f}", f"{longitude:.2f}"


def parse_forecast(document):
    first = document["properties"]["timeseries"][0]
    data = first["data"]
    hourly = data.get("next_1_hours", {})
    return Forecast(first["time"], float(data["instant"]["details"]["air_temperature"]),
                    hourly.get("summary", {}).get("symbol_code"),
                    hourly.get("details", {}).get("precipitation_amount"))


def refresh_time(headers, now):
    next_request = now + RETRY_AFTER
    expires = headers.get("Expires")
    if expires:
        try:
            parsed = parsedate_to_datetime(expires)
            if parsed.tzinfo is not None:
                next_request = max(next_request, parsed)
        except (TypeError, ValueError):
            pass
    return next_request


def fetch_weather(latitude, longitude, previous=None, *, now=None, opener=urlopen):
    location = coordinates(latitude, longitude)
    now = datetime.now(timezone.utc) if now is None else now
    same_location = previous is not None and previous.location == location
    if same_location and now < previous.refresh_at:
        return previous

    url = PROVIDER + "?" + urlencode(dict(zip(("lat", "lon"), location)))
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if same_location and previous.last_modified:
        headers["If-Modified-Since"] = previous.last_modified
    try:
        with opener(Request(url, headers=headers), timeout=12) as response:
            payload = response.read(1024 * 1024 + 1)
            if len(payload) > 1024 * 1024:
                raise ValueError("Weather provider returned an oversized response.")
            forecast = parse_forecast(json.loads(payload))
            return WeatherCache(location, forecast, refresh_time(response.headers, now),
                                response.headers.get("Last-Modified"))
    except HTTPError as error:
        if error.code != 304 or not same_location:
            raise
        return WeatherCache(location, previous.forecast, refresh_time(error.headers, now),
                            previous.last_modified)


def read_cache(path):
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        expiry = datetime.fromisoformat(data["refresh_at"])
        if expiry.tzinfo is None:
            return None
        return WeatherCache(tuple(data["location"]), Forecast(**data["forecast"]),
                            expiry, data["last_modified"])
    except (OSError, ValueError, TypeError, KeyError):
        return None


def write_cache(path, cache):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    data = asdict(cache)
    data["refresh_at"] = cache.refresh_at.isoformat()
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream)
            stream.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("latitude", type=float)
    parser.add_argument("longitude", type=float)
    parser.add_argument("--cache", action="store_true", help="Reuse the last forecast stored in the user cache")
    parser.add_argument("--card", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    cache_root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    cache_path = cache_root / "shadowrealm-os" / "weather.json"
    previous = read_cache(cache_path) if args.cache else None
    stale = False
    location = None
    try:
        location = coordinates(args.latitude, args.longitude)
        result = fetch_weather(args.latitude, args.longitude, previous)
    except (OSError, ValueError, KeyError, IndexError) as error:
        if not args.card or previous is None or previous.location != location:
            parser.exit(1, f"Weather unavailable: {error}\n")
        result = previous
        stale = True
    if args.cache and result is not previous:
        try:
            write_cache(cache_path, result)
        except OSError:
            pass
    forecast = result.forecast
    if args.card:
        condition = (forecast.condition or "Forecast").split("_", 1)[0]
        labels = {"fair": "Mostly clear", "clearsky": "Clear sky", "partlycloudy": "Partly cloudy",
                  "cloudy": "Cloudy", "rain": "Rain", "lightrain": "Light rain",
                  "heavyrain": "Heavy rain", "snow": "Snow", "fog": "Fog", "sleet": "Sleet"}
        print(f"{forecast.temperature_c:.1f} °C")
        print("Offline · cached forecast" if stale else labels.get(condition, "Forecast available"))
        print("stale" if stale else "fresh")
    else:
        print(json.dumps(asdict(forecast), ensure_ascii=False))


if __name__ == "__main__":
    main()
