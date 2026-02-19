#!/usr/bin/env python3
"""Generate ASX AI app icons with a stylish 'A' letter on gradient background."""
import struct
import zlib
import os

def create_png(width, height, pixels):
    """Create a PNG file from raw RGBA pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    
    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter byte
        for x in range(width):
            idx = (y * width + x) * 4
            raw += bytes(pixels[idx:idx+4])
    
    compressed = zlib.compress(raw, 9)
    
    return signature + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')


def draw_icon(size):
    """Draw the ASX AI icon with gradient background and bold 'A' letter."""
    pixels = [0] * (size * size * 4)
    
    # Corner radius
    radius = size // 6
    
    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            
            # Rounded rectangle check
            in_rect = True
            # Top-left corner
            if x < radius and y < radius:
                if (x - radius) ** 2 + (y - radius) ** 2 > radius ** 2:
                    in_rect = False
            # Top-right corner
            if x >= size - radius and y < radius:
                if (x - (size - radius - 1)) ** 2 + (y - radius) ** 2 > radius ** 2:
                    in_rect = False
            # Bottom-left corner
            if x < radius and y >= size - radius:
                if (x - radius) ** 2 + (y - (size - radius - 1)) ** 2 > radius ** 2:
                    in_rect = False
            # Bottom-right corner
            if x >= size - radius and y >= size - radius:
                if (x - (size - radius - 1)) ** 2 + (y - (size - radius - 1)) ** 2 > radius ** 2:
                    in_rect = False
            
            if not in_rect:
                pixels[idx] = 0
                pixels[idx+1] = 0
                pixels[idx+2] = 0
                pixels[idx+3] = 0
                continue
            
            # Gradient background: top-left (#00d4aa) to bottom-right (#00b894)
            t = (x + y) / (2 * size)
            r = int(0 * (1 - t) + 0 * t)
            g = int(212 * (1 - t) + 184 * t)
            b = int(170 * (1 - t) + 148 * t)
            
            # Add subtle radial glow in center
            cx, cy = size / 2, size / 2
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            max_dist = (cx ** 2 + cy ** 2) ** 0.5
            glow = max(0, 1 - dist / max_dist) * 0.3
            r = min(255, int(r + glow * 40))
            g = min(255, int(g + glow * 30))
            b = min(255, int(b + glow * 20))
            
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b
            pixels[idx+3] = 255
    
    # Draw the letter "A" - dark color on the gradient
    # Using a bold geometric A design
    cx = size / 2
    cy = size / 2
    letter_h = size * 0.55  # letter height
    letter_w = size * 0.42  # letter width
    stroke = max(2, size // 12)  # stroke width
    
    top_y = cy - letter_h / 2
    bot_y = cy + letter_h / 2
    left_x = cx - letter_w / 2
    right_x = cx + letter_w / 2
    
    # Draw the A character pixel by pixel
    for y in range(size):
        for x in range(size):
            draw = False
            fy = float(y)
            fx = float(x)
            
            # Check if pixel is inside the A shape
            if fy >= top_y and fy <= bot_y:
                progress = (fy - top_y) / (bot_y - top_y)  # 0 at top, 1 at bottom
                
                # Left leg of A
                leg_x = left_x + (cx - left_x) * (1 - progress)  # converges to center at top
                if abs(fx - leg_x) < stroke:
                    draw = True
                
                # Right leg of A
                leg_x_r = right_x - (right_x - cx) * (1 - progress)
                if abs(fx - leg_x_r) < stroke:
                    draw = True
                
                # Crossbar of A (at ~45% from top)
                crossbar_y = top_y + letter_h * 0.55
                if abs(fy - crossbar_y) < stroke * 0.8:
                    # Crossbar spans between the two legs at this height
                    cb_progress = (crossbar_y - top_y) / (bot_y - top_y)
                    cb_left = left_x + (cx - left_x) * (1 - cb_progress)
                    cb_right = right_x - (right_x - cx) * (1 - cb_progress)
                    if fx >= cb_left - stroke * 0.5 and fx <= cb_right + stroke * 0.5:
                        draw = True
                
                # Top peak connection (make it pointed/sharp)
                if progress < 0.08:
                    peak_width = stroke * (1 + progress * 3)
                    if abs(fx - cx) < peak_width:
                        draw = True
            
            if draw:
                idx = (y * size + x) * 4
                # Only draw if we're inside the rounded rect (alpha > 0)
                if pixels[idx+3] > 0:
                    # Dark color for the letter
                    pixels[idx] = 8    # dark-900 r
                    pixels[idx+1] = 11  # dark-900 g
                    pixels[idx+2] = 18  # dark-900 b
                    pixels[idx+3] = 255
    
    return pixels


# Generate icons
os.makedirs('frontend/public/icons', exist_ok=True)

for size, path in [(192, 'frontend/public/icons/icon-192.png'), 
                    (512, 'frontend/public/icons/icon-512.png'),
                    (180, 'frontend/public/apple-touch-icon.png')]:
    pixels = draw_icon(size)
    png_data = create_png(size, size, pixels)
    with open(path, 'wb') as f:
        f.write(png_data)
    print(f'Created {path} ({len(png_data)} bytes)')

# Also create a favicon (32x32)
pixels = draw_icon(32)
png_data = create_png(32, 32, pixels)
with open('frontend/public/favicon.png', 'wb') as f:
    f.write(png_data)
print(f'Created favicon.png ({len(png_data)} bytes)')

print('All icons generated!')
