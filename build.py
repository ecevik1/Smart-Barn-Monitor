import PyInstaller.__main__
import os
import site

# Get site-packages wsdl path
site_packages = [p for p in site.getsitepackages() if 'site-packages' in p][0]
wsdl_path = os.path.join(site_packages, 'wsdl')

PyInstaller.__main__.run([
    'src/main.py',
    '--name=Smart Barn Monitor',
    '--windowed',
    '--noconfirm',
    '--onefile',
    f'--add-data={wsdl_path};wsdl'
])
