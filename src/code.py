import os
import board
import busio
import gc9a01
import time
import terminalio
import displayio
import sdcardio
import storage

# Release any resources currently in use for the displays
displayio.release_displays()

# SPI and SD card setup
spi = busio.SPI(board.D14, MOSI=board.D15, MISO=board.D2)

try:
    sdcard = sdcardio.SDCard(spi, board.D13)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except OSError as e:
    print("Failed to mount SD card:", e)
    while True:
        pass  # Stop execution if SD card fails

bmpfiles = sorted("/sd/" + fn for fn in os.listdir("/sd") if fn.lower().endswith("bmp"))
if len(bmpfiles) == 0:
    print("No BMP files found")
    while True:
        pass  # Halt if no BMP files found

# Time in seconds between images
img_time = 10

# gc9a01 pins
tft_clk = board.D14
tft_mosi = board.D15
tft_rst = board.D33
tft_dc = board.D27
tft_cs = board.D5
tft_bl = board.D32

# Display setup
display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst)
display = gc9a01.GC9A01(display_bus, width=240, height=240, backlight_pin=tft_bl)

# Main display context
main = displayio.Group()
display.root_group = main

# Pre-cache the first image to start
current_bitmap = displayio.OnDiskBitmap(bmpfiles[0])
current_tile_grid = displayio.TileGrid(current_bitmap, pixel_shader=current_bitmap.pixel_shader)
main.append(current_tile_grid)

# Start from the first image
current_index = 0

while True:
    # Determine the next index (loop around when reaching the end)
    next_index = (current_index + 1) % len(bmpfiles)
    next_filename = bmpfiles[next_index]

    # Pre-cache the next image for smoother transitions
    try:
        next_bitmap = displayio.OnDiskBitmap(next_filename)
        next_tile_grid = displayio.TileGrid(next_bitmap, pixel_shader=next_bitmap.pixel_shader)
    except Exception as e:
        print(f"Failed to cache {next_filename}: {e}")
        continue

    # Wait for the duration of the current image display
    time.sleep(img_time)

    # Swap the images: remove the current image, and append the pre-cached next image
    main.remove(current_tile_grid)
    main.append(next_tile_grid)

    # Update current image to the next one
    current_tile_grid = next_tile_grid
    current_index = next_index
