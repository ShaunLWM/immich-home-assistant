# Immich x Home Assistant

> Fork of [outadoc/immich-home-assistant](https://github.com/outadoc/immich-home-assistant) with fixes for Immich 3.x compatibility and reliability improvements.

This custom integration for Home Assistant allows you to display random pictures from your Immich instance right inside your dashboards.

## Changes from upstream

- **Fix: Immich 3.x compatibility** -- `isFavorite` now sent as boolean in JSON body instead of string in form data
- **Fix: Reusable HTTP session** -- single `aiohttp.ClientSession` with 30s timeout instead of creating one per API call
- **Fix: Session cleanup** -- sessions properly closed on integration unload and config flow completion
- **Fix: Infinite download loop** -- image download retries capped at 5 attempts with logging
- **Fix: Race condition** -- `asyncio.Lock` prevents concurrent image downloads from racing
- **Fix: Timezone-aware datetimes** -- uses `datetime.now(tz=timezone.utc)` throughout
- **Improvement: Server-side image filter** -- sends `type: IMAGE` in API payload to reduce unnecessary data transfer

## Installation

### HACS (Custom Repository)

1. Open HACS in Home Assistant
2. Click the three dots menu (top right) and select **Custom repositories**
3. Add `https://github.com/ShaunLWM/immich-home-assistant` with category **Integration**
4. Search for "Immich" in HACS and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/immich` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Usage

As a suggestion, you could use this integration to create a picture frame. You can create a "panel" dashboard, and display your picture entity inside of it:

```yaml
type: panel
title: Photo frame
path: photo-frame
icon: mdi:image-frame
subview: true
cards:
  - type: picture-entity
    entity: image.immich_favorite_image
    show_state: false
    show_name: false
    aspect_ratio: "16:9"
    fit_mode: contain
```

You can then use this dashboard on a dedicated device in kiosk mode.

## How does it work?

The integration provides multiple `image` entities, each corresponding to an album. Each entity switches to a new random image every 5 minutes.

These entities can be displayed using standard Lovelace cards -- for example, the `picture` or `picture-entity` cards.

## Configuration

You can set up the Immich integration from the Home Assistant UI:

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Immich**
3. Enter your Immich instance URL and API key

You can generate an API key from your **Account Settings** on your Immich instance.

### Exposing other albums

By default, only the "Favorites" album is exposed as an entity.

You can expose more albums on the integration's options page.

> **Note:** Exposing many albums will increase resource usage on your Home Assistant machine and the number of API calls to your Immich instance.
