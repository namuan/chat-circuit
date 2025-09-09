import sys
import os
from PyInstaller.utils.hooks import collect_data_files
import site

block_cipher = None

# Find the site-packages directory
site_packages = site.getsitepackages()[0]

# Construct the path to the tokenizer file
tokenizer_path = os.path.join(site_packages, 'litellm', 'litellm_core_utils', 'tokenizers', 'anthropic_tokenizer.json')

a = Analysis(['main.py'],
             pathex=['.'],
             binaries=None,
             datas=[
                  ('resources', 'resources'),
                  (tokenizer_path, 'litellm/litellm_core_utils/tokenizers'),
                  ('models.conf', '.')
              ],
             hiddenimports=['tiktoken_ext.openai_public', 'tiktoken_ext'],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='app',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='resources\\icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='ChatCircuit')

app = BUNDLE(coll,
             name='ChatCircuit.app',
             icon='resources/icon.icns',
             bundle_identifier='com.github.namuan.chatcircuit',
             info_plist={
                'CFBundleName': 'ChatCircuit',
                'CFBundleVersion': '1.0.0',
                'CFBundleShortVersionString': '1.0.0',
                'NSPrincipalClass': 'NSApplication',
                'NSHighResolutionCapable': 'True'
                }
             )
