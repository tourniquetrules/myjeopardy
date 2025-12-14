#!/usr/bin/env python3
"""
A simple script to generate a QR code for a given URL.
"""

import qrcode

def main():
    """Main function to generate QR code from user input URL."""
    url = input("Enter the URL you want to encode in the QR code: ")
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create an image from the QR Code instance
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image to a file
    filename = "qr_code.png"
    img.save(filename)
    print(f"QR code generated successfully and saved as {filename}")

if __name__ == "__main__":
    main()