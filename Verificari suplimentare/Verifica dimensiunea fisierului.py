import os
file_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro\python-scripts-examples.html'
size_bytes = os.path.getsize(file_path)
size_mb = size_bytes / (1024 * 1024)
print(f"Dimensiune: {size_mb:.2f} MB ({size_bytes:,} bytes)")