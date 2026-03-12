# BlindCtrl - Home Assistant Integration

A custom Home Assistant integration for controlling BLE smart blinds via a Raspberry Pi hub running the BlindCtrl dashboard.

## Features

- Automatic discovery of all configured blinds from the BlindCtrl hub
- Each blind appears as a **cover** entity with full position control (0-100%)
- Devices are grouped by room automatically
- Online/offline status reflected in entity availability
- Polling-based updates every 30 seconds

## Installation via HACS

1. Open HACS in your Home Assistant instance
2. Click the three dots menu in the top right corner
3. Select **Custom repositories**
4. Add your repository URL and select **Integration** as the category
5. Click **Add**
6. Search for **BlindCtrl** and install it
7. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for **BlindCtrl**
4. Enter the IP address of your Raspberry Pi running the BlindCtrl dashboard
5. The integration will discover all identified blinds and create cover entities

## Requirements

- A Raspberry Pi running the BlindCtrl dashboard and API
- The Pi must be accessible on your local network
- Blinds must be identified and configured in the BlindCtrl dashboard before they appear in Home Assistant

## Entities

Each identified blind is registered as a `cover` entity with:

| Feature | Description |
|---------|-------------|
| Open | Sets blind to fully open (position 200) |
| Close | Sets blind to fully closed (position 0) |
| Set Position | Sets blind to any position (0-100% mapped to 0-200) |
| Stop | Holds current position |

## Troubleshooting

- **Cannot connect**: Verify the Pi's IP address and that BlindCtrl is running on port 5000
- **Blinds not showing**: Make sure blinds are marked as "identified" in the BlindCtrl dashboard
- **Offline status**: The blind's BLE connection may be unavailable; check the dashboard
