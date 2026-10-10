# HTTP Server Approach for Macropad Control

## Problem

The current HID-based service is unreliable due to permission issues with `/dev/hidraw*` devices and device detection problems on Raspberry Pi.

## Solution

Create a simple HTTP server that exposes projector control endpoints, and a keyboard listener service that captures F1-F12 keys from the macropad and makes HTTP requests to the server.

## Architecture

1. **HTTP Server** (`macropad/projector_api_server.py`)

   - Flask-based REST API server
   - Endpoints: `/api/power/all/on`, `/api/power/all/off`, `/api/mute/front/on`, etc.
   - Runs on localhost (127.0.0.1:5000)
   - Uses existing `ProjectorManager` for control

2. **Keyboard Listener Service** (`macropad/http_macropad_service.py`)

   - Uses evdev to capture F1-F12 keys from macropad
   - Maps keys to HTTP requests
   - Makes HTTP POST requests to the API server
   - More reliable than raw HID (no permission issues)

3. **Systemd Services**

   - `projector-api.service` - Runs the HTTP server
   - `macropad-http.service` - Runs the keyboard listener

4. **Macropad Firmware** (`macropad/code.py`)

   - Already sends F1-F12 keys (keyboard mode)
   - No changes needed if using keyboard mode
   - Or ensure it's in keyboard mode instead of raw HID

## Implementation Steps

### Step 1: Create HTTP API Server

- Create `macropad/projector_api_server.py` with Flask
- Endpoints:
  - `POST /api/power/all/on` - Turn all projectors on
  - `POST /api/power/all/off` - Turn all projectors off
  - `POST /api/mute/front/on` - Blank front projectors
  - `POST /api/mute/front/off` - Unblank front projectors
  - `POST /api/freeze/front/on` - Freeze front projectors
  - `POST /api/freeze/front/off` - Unfreeze front projectors
  - `GET /api/status` - Get all projector status
- Returns JSON responses
- Uses existing `ProjectorManager` class

### Step 2: Create HTTP-Based Keyboard Listener

- Create `macropad/http_macropad_service.py`
- Uses evdev to listen for F1-F12 keys
- Maps keys to API endpoints:
  - F1 → `/api/power/all/on`
  - F2 → `/api/power/all/off`
  - F3 → `/api/mute/front/on`
  - F4 → `/api/mute/front/off`
  - F5 → `/api/freeze/front/on`
  - F6 → `/api/freeze/front/off`
- Makes HTTP POST requests using `requests` library
- Handles connection errors gracefully

### Step 3: Update Macropad Firmware

- Ensure `macropad/code.py` sends keyboard events (F1-F12)
- Already does this in fallback mode, but ensure it's the primary mode
- Remove dependency on raw HID if not needed

### Step 4: Create Systemd Services

- Update `scripts/create_macropad_service.sh` or create new script
- Create two services:

  1. `projector-api.service` - HTTP server (starts first)
  2. `macropad-http.service` - Keyboard listener (depends on API server)

### Step 5: Update Documentation

- Update `docs/MACROPAD_SETUP.md` with new HTTP-based approach
- Add troubleshooting section
- Document how to test with curl

## Benefits

- ✅ No HID permission issues (uses evdev which is more reliable)
- ✅ Easy to test (can use `curl` to test endpoints)
- ✅ Easy to debug (HTTP requests are visible in logs)
- ✅ Can add web interface later
- ✅ Can be accessed remotely if needed
- ✅ Clean separation of concerns
- ✅ More reliable on Raspberry Pi

## Testing

1. Test API server directly:
   ```bash
   curl -X POST http://localhost:5000/api/power/all/on
   ```

2. Test keyboard listener:

   - Press F1-F12 keys and verify HTTP requests are made

3. Test full integration:

   - Start both services and press macropad buttons

## Files to Create/Modify

- **New**: `macropad/projector_api_server.py` - HTTP API server
- **New**: `macropad/http_macropad_service.py` - Keyboard listener with HTTP
- **Modify**: `macropad/code.py` - Ensure keyboard mode is primary
- **New**: `scripts/create_http_macropad_service.sh` - Service setup script
- **Modify**: `docs/MACROPAD_SETUP.md` - Update with HTTP approach
- **New**: `requirements.txt` - Add Flask and requests if not present