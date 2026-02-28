"""
Sample Skill: Weather Lookup

Demonstrates the @tool decorator pattern for creating OmniClaw skills.
Place custom skills in ~/.omniclaw/skills/ and they'll be auto-loaded.
"""

from core.skills.registry import tool


@tool(
    name="weather_lookup",
    description="Look up current weather for a city. Returns temperature, conditions, and forecast.",
    parameters={
        "city": {
            "type": "string",
            "description": "City name (e.g., 'London', 'New York', 'Tokyo')",
        },
        "units": {
            "type": "string",
            "description": "Temperature units: 'celsius' or 'fahrenheit'",
            "enum": ["celsius", "fahrenheit"],
        },
    },
    required=["city"],
)
async def weather_lookup(city: str, units: str = "celsius") -> str:
    """
    Look up weather for a city.

    This is a sample skill — replace with a real weather API integration.
    """
    # Placeholder response — integrate with OpenWeatherMap, WeatherAPI, etc.
    return (
        f"Weather for {city}:\n"
        f"  Temperature: 22°{'C' if units == 'celsius' else 'F'}\n"
        f"  Conditions: Partly cloudy\n"
        f"  Humidity: 65%\n"
        f"  Wind: 12 km/h NW\n"
        f"\nNote: This is a sample skill. Replace with a real API integration."
    )
