import struct

W = 48


def pixel(x, y):
    """Return (B, G, R, A) for pixel at (x, y)."""
    b = g = r = a = 0

    # left document (blue)
    if 4 <= x <= 20 and 3 <= y <= 44:
        inside = 5 <= x <= 19 and 5 <= y <= 43
        if not inside:
            b, g, r, a = 60, 100, 180, 255
        elif y in (11, 12, 18, 19, 25, 26) and 7 <= x <= 17:
            b, g, r, a = 60, 100, 180, 255
        else:
            b, g, r, a = 225, 235, 255, 255

    # right document (green)
    if 27 <= x <= 43 and 3 <= y <= 44:
        inside = 28 <= x <= 42 and 5 <= y <= 43
        if not inside:
            b, g, r, a = 60, 170, 100, 255
        elif y in (11, 12, 18, 19, 25, 26) and 30 <= x <= 40:
            b, g, r, a = 60, 170, 100, 255
        else:
            b, g, r, a = 225, 255, 235, 255

    # arrow (orange)
    if (y in range(19, 26) and x in (22, 23, 24, 25)):
        b, g, r, a = 50, 160, 255, 255
    if (x in (23, 24) and y in range(20, 25)):
        b, g, r, a = 50, 160, 255, 255

    return b, g, r, a


def create_ico(path):
    # XOR mask: bottom-up BGRA pixels
    xor_pixels = bytearray()
    for y in range(W - 1, -1, -1):
        for x in range(W):
            xor_pixels.extend(pixel(x, y))

    # AND mask: bottom-up, 1 bpp, padded to 4 bytes per row
    row_bytes = ((W + 31) // 32) * 4
    and_mask = bytearray()
    for y in range(W - 1, -1, -1):
        row = bytearray(row_bytes)
        for x in range(W):
            _, _, _, a = pixel(x, y)
            if a == 0:  # transparent → AND mask bit = 1
                byte_idx = x // 8
                bit_idx = 7 - (x % 8)
                row[byte_idx] |= (1 << bit_idx)
        and_mask.extend(row)

    image_data = xor_pixels + and_mask

    # BITMAPINFOHEADER (height is 2 * W for ICO XOR+AND mask)
    bmp_header = struct.pack(
        '<IiiHHIIiiII',
        40, W, W * 2, 1, 32, 0,
        len(image_data), 0, 0, 0, 0
    )

    full_data = bmp_header + image_data
    data_size = len(full_data)

    with open(path, 'wb') as f:
        f.write(struct.pack('<HHH', 0, 1, 1))   # ICO header
        f.write(struct.pack(
            '<BBBBHHII',
            W if W < 256 else 0,
            W if W < 256 else 0,
            0, 0, 1, 32, data_size, 22
        ))                                       # directory entry
        f.write(full_data)

    print(f"Icon created: {path} ({W}x{W})")


if __name__ == "__main__":
    create_ico("app.ico")
