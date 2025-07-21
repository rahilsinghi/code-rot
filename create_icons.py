#!/usr/bin/env python3
"""
Generate placeholder PWA icons and favicon
"""

import os
from pathlib import Path

def create_svg_icon(size, filename):
    """Create a simple SVG icon"""
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
    <rect width="{size}" height="{size}" fill="#007bff"/>
    <rect x="{size//8}" y="{size//8}" width="{size*3//4}" height="{size*3//4}" fill="#ffffff" rx="{size//8}"/>
    <text x="{size//2}" y="{size//2}" text-anchor="middle" dominant-baseline="middle" 
          font-family="Arial, sans-serif" font-size="{size//4}" font-weight="bold" fill="#007bff">
        {'&lt;/&gt;' if size >= 128 else 'CP'}
    </text>
</svg>'''
    
    with open(filename, 'w') as f:
        f.write(svg_content)

def create_favicon():
    """Create a simple favicon"""
    favicon_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
    <rect width="32" height="32" fill="#007bff"/>
    <rect x="4" y="4" width="24" height="24" fill="#ffffff" rx="4"/>
    <text x="16" y="16" text-anchor="middle" dominant-baseline="middle" 
          font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#007bff">
        CP
    </text>
</svg>'''
    
    with open('static/icons/favicon.ico', 'w') as f:
        f.write(favicon_content)

def main():
    # Create icons directory
    icons_dir = Path('static/icons')
    icons_dir.mkdir(exist_ok=True)
    
    # Create PWA icons
    create_svg_icon(192, 'static/icons/icon-192x192.png')
    create_svg_icon(512, 'static/icons/icon-512x512.png')
    
    # Create favicon
    create_favicon()
    
    print("✅ Created placeholder icons:")
    print("  📱 icon-192x192.png")  
    print("  📱 icon-512x512.png")
    print("  🌐 favicon.ico")
    print("\n💡 These are placeholder SVG files.")
    print("   For production, replace with actual PNG/ICO files.")

if __name__ == "__main__":
    main() 