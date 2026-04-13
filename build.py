import PyInstaller.__main__
import os
import site

# Get site-packages wsdl path
site_packages = [p for p in site.getsitepackages() if 'site-packages' in p][0]
wsdl_path = os.path.join(site_packages, 'wsdl')

PyInstaller.__main__.run([
    'main.py',
    '--name=Barn Monitor v1.2',
    '--windowed',
    '--onedir', 
    '--noconfirm',
    '--clean',
    '--icon=assets/icon.png',
    '--add-data=assets;assets',
    f'--add-data={wsdl_path};wsdl'
])
