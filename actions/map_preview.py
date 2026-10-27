from __future__ import annotations

from urllib.parse import quote_plus


def map_preview(parameters: dict, player=None) -> str:
    place = str((parameters or {}).get("place") or "").strip()
    if not place:
        return "Please specify a place to show on the map."
    zoom = parameters.get("zoom", 13)
    try:
        zoom = max(3, min(19, int(zoom)))
    except (TypeError, ValueError):
        zoom = 13
    # Geocoding and OSM tile loading happen asynchronously in the embedded UI.
    # This keeps slow network requests from stalling the live assistant cycle.
    url = f"https://www.openstreetmap.org/search?query={quote_plus(place)}#map={zoom}"
    if player is not None and hasattr(player, "show_map_preview"):
        player.show_map_preview(place, url)
        return f"Map preview is open in the Mark LVI display for {place}."
    return "The in-app map display is unavailable right now."


TOOL = {
    "name": "map_preview",
    "description": "Shows an interactive map inside the Mark LVI display. Use when the user asks to see, find, or open a location on a map.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "place": {"type": "STRING", "description": "Location, address, or place to show"},
            "zoom": {"type": "INTEGER", "description": "Map zoom level from 3 to 19; optional"},
        },
        "required": ["place"],
    },
    "handler": map_preview,
}

