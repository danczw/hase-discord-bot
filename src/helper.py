import logging
import random
from datetime import datetime, timedelta

import requests


def get_server_info(ctx) -> str:
    """creates a message with server info

    Args:
        ctx (ctx): discord context

    Returns:
        str: message displayed to user with server info
    """
    _line_break = "- - - -"
    _server_name = f"**Server name:** {ctx.guild}"
    _server_owner = f"**Server owner:** {ctx.guild.owner}:"
    _member_count = f"**Members:** {ctx.guild.member_count}"

    n_text_channels = len([channel for channel in ctx.guild.text_channels])
    _text_channels = f"**Text Channels**: {n_text_channels}"

    n_voice_channels = len([channel for channel in ctx.guild.voice_channels])
    _voice_channels = f"**Voice Channels**: {n_voice_channels}"

    response = "\n".join([
        _server_name, _server_owner,
        _line_break,
        _member_count,
        _text_channels,
        _voice_channels,
    ])

    return response


def get_weather_info(ctx, location: str, KEYS: dict, logger: logging.Logger) -> str:
    """gets weather info for a location and creates a message

    Args:
        ctx (_type_): discord context
        location (str): location name of weather conditions request
        KEYS (dict): dictionary of API keys

    Returns:
        str: message displayed to user with weather conditions for a location
    """
    # get geolocation data
    try:
        geo_url = f"https://dev.virtualearth.net/REST/v1/Locations?q=" \
            f"{location}&key={KEYS['BINGMAPS_API_KEY']}"
        geo_response = requests.get(geo_url)
    except requests.exceptions.RequestException as error:
        logger.error(error)
        return "I don't know where that is."

    geo_json = geo_response.json()
    # pprint(geo_json)

    # extract relevant geolocation data
    location = geo_json[
        "resourceSets"][0]["resources"][0]["address"]["formattedAddress"]
    lat = geo_json[
        "resourceSets"][0]["resources"][0]["point"]["coordinates"][0]
    lng = geo_json[
        "resourceSets"][0]["resources"][0]["point"]["coordinates"][1]

    if lat is None or lng is None:
        return "I don't know where that is."

    # get weather data
    try:
        exclude = "minutely,hourly,alerts"
        weather_url = f"https://api.openweathermap.org/data/3.0/onecall?" \
            f"lat={lat}&lon={lng}&exclude={exclude}" \
            f"&appid={KEYS['OPENWEATHER_API_KEY']}&units=metric"
        weather_response = requests.get(weather_url)
    except requests.exceptions.RequestException as error:
        logger.error(error)
        return "I don't know where that is."

    # extract relevant weather data
    weather_json = weather_response.json()
    message = create_weather_message(weather_json, location)

    return message


def create_weather_message(weather_json, location: str) -> str:
    """extracts relevant weather data from json and creates a message

    Args:
        weather_json (str, json): json of weather conditions for a location
        location (str): location name of weather conditions request

    Returns:
        str: message displayed to user with weather conditions for a location
    """
    decimal_round = 1
    daylightsaving = 1

    # current weather
    curr_condition = weather_json['current']['weather'][0]['description']
    curr_temp = round(weather_json['current']['temp'], decimal_round)
    curr_temp_feels_like = round(weather_json['current']['feels_like'], decimal_round)
    curr_humidity = weather_json['current']['humidity']

    # todays weather
    today_condition = weather_json['daily'][0]['weather'][0]['description']
    today_temp_max = round(weather_json['daily'][0]['temp']['max'], decimal_round)
    today_temp_min = round(weather_json['daily'][0]['temp']['min'], decimal_round)
    today_sunrise = (
        datetime.fromtimestamp(weather_json['daily'][0]['sunrise'] + weather_json['timezone_offset'])
        - timedelta(hours=daylightsaving)
    ).strftime('%H:%M')
    today_sunset = (
        datetime.fromtimestamp(weather_json['daily'][0]['sunset'] + weather_json['timezone_offset'])
        - timedelta(hours=daylightsaving)
    ).strftime('%H:%M')

    # tomorrow weather
    tomorrow_condition = weather_json['daily'][1]['weather'][0]['description']
    tomorrow_temp_max = round(weather_json['daily'][1]['temp']['max'], decimal_round)
    tomorrow_temp_min = round(weather_json['daily'][1]['temp']['min'], decimal_round)
    tomorrow_sunrise = (
        datetime.fromtimestamp(weather_json['daily'][1]['sunrise'] + weather_json['timezone_offset'])
        - timedelta(hours=daylightsaving)
    ).strftime('%H:%M')
    tomorrow_sunset = (
        datetime.fromtimestamp(weather_json['daily'][1]['sunset'] + weather_json['timezone_offset'])
        - timedelta(hours=daylightsaving)
    ).strftime('%H:%M')

    # condition to icon
    curr_condition_icon = condition_to_icon(weather_json['current']['weather'][0]['id'])
    today_condition_icon = condition_to_icon(weather_json['daily'][0]['weather'][0]['id'])
    tomorrow_condition_icon = condition_to_icon(weather_json['daily'][1]['weather'][0]['id'])

    # create bot response message
    message = \
        f"\n**Weather for {location}**\n" \
        f"{curr_condition_icon} Currently {curr_condition} with {curr_temp}°C, \n" \
        f"feels like {curr_temp_feels_like}°C and {curr_humidity}% humidity.\n\n" \
        f"{today_condition_icon} **Today: {today_condition}**\n" \
        f"Low: {today_temp_min}°C -- High: {today_temp_max}°C\n" \
        f"Sunrise: {today_sunrise}h -- Sunset: {today_sunset}h\n\n" \
        f"{tomorrow_condition_icon} **Tomorrow: {tomorrow_condition}**\n" \
        f"Low: {tomorrow_temp_min}°C -- High: {tomorrow_temp_max}°C\n" \
        f"Sunrise: {tomorrow_sunrise}h -- Sunset: {tomorrow_sunset}h\n"

    return message


def condition_to_icon(condition_id: int) -> str:
    """converts openweathermap condition id to discord icon

    Args:
        condition_id (int): openweathermap weather condition id

    Returns:
        str: discord icon string
    """
    if condition_id >= 200 and condition_id < 300:
        icon_str = ":thunder_cloud_rain:"
    elif condition_id >= 300 and condition_id < 400:
        icon_str = ":cloud_rain:"
    elif condition_id == 500:
        icon_str = ":white_sun_rain_cloud:"
    elif condition_id >= 501 and condition_id < 600:
        icon_str = ":cloud_rain:"
    elif condition_id >= 600 and condition_id < 700:
        icon_str = ":cloud_snow:"
    elif condition_id >= 700 and condition_id < 800:
        icon_str = ":fog:"
    elif condition_id == 800:
        icon_str = ":sunny:"
    elif condition_id == 801:
        icon_str = ":white_sun_cloud:"
    elif condition_id > 801 and condition_id < 900:
        icon_str = ":cloud:"
    else:
        icon_str = ":question:"

    return icon_str


def get_dice_results(n_rolls: int = 1) -> str:
    """rolls dice and returns results

    Args:
        n_rolls (int, optional): number of dice rolls. Defaults to 1.

    Returns:
        str: string of dice results
    """
    if n_rolls > 10:
        return "I only have 10 dice."
    else:
        _dice = [str(random.choice(range(1, 7))) for throw in range(n_rolls)]
        return ", ".join(_dice)


def get_crypto_data(_coin: str, logger: logging.Logger) -> str:
    """Gets crypto data from coingecko API

    Args:
        _coin (str): crypto currency name
        logger (logging.Logger): logger object

    Returns:
        str: Message with crypto data or error message

    TODO: view /coins/{id} for more data
    - https://www.coingecko.com/en/api/documentation
    """
    coin_id = _coin.lower()

    # get coin data from id
    coin_data_url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=eur'
    try:
        coin_data_response = requests.get(coin_data_url)
        logger.info(f"Coin data received for {coin_id}")
        response = f"**{coin_id.title()}**: {coin_data_response.json()[coin_id]['eur']}€"
        return response

    except requests.exceptions.RequestException as error:
        logger.error(error)
        return "I can't find you symbol, are you sure it is correct?"


def get_holiday_data(logger: logging.Logger, _country: str = 'DE') -> str:
    """_summary_

    Args:
        logger (logging.Logger): logger object
        _country (str, optional): country code for holiday data. Defaults to 'DE'.
    Returns:
        str: Message with holiday data or error message
    """
    country_code = _country.upper()

    # get current year
    curr_year = datetime.now().year

    # get holiday data from country code
    holiday_data_url = f'https://date.nager.at/api/v3/publicholidays/{curr_year}/{country_code}'
    try:
        holiday_data_response = requests.get(holiday_data_url)
        logger.info(f"Holiday data received for {country_code}")

        # create response message
        response = f"**Holidays for {country_code}**\n"
        for holiday in holiday_data_response.json():
            # extract counties from response
            if holiday['counties']:
                counties = ', '.join([county.split('-')[1] for county in holiday['counties']])
                counties = f" ({counties})\n"
            else:
                counties = '\n'

            row = f"{holiday['date']} - {holiday['name']}" + counties
            response += row

        return response

    except requests.exceptions.RequestException as error:
        logger.error(error)
        return "I can't find your country, are you sure it is a correct country code?"