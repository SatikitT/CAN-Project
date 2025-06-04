def can_crc15(bitstream):
    poly = 0xC599
    crc = 0x0000

    for bit in bitstream:
        topbit = (crc >> 14) & 1
        crc = ((crc << 1) | bit) & 0x7FFF  # 15-bit mask
        if topbit:
            crc ^= poly
    return crc

bits = b'1 0000 0000 0100 0000'

bits2 = b'011000111111111111111111111011101000000'
# [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0]
print(bin(can_crc15(bits)))