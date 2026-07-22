# xAIPM_App.spec
from PyInstaller.utils.hooks import collect_all, copy_metadata
import streamlit_quill, os

datas = []
binaries = []
hiddenimports = []

for pkg in ['streamlit', 'streamlit_quill', 'PIL']:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

datas += copy_metadata('streamlit')
datas += copy_metadata('streamlit-quill')
datas += copy_metadata('Pillow')

quill_pkg_dir = os.path.dirname(streamlit_quill.__file__)
quill_frontend = os.path.join(quill_pkg_dir, 'frontend', 'build')
if os.path.exists(quill_frontend):
    datas += [(quill_frontend, os.path.join('streamlit_quill', 'frontend', 'build'))]

datas += [
    ('xAIPM.py', '.'),
    ('BlueprintTemplate.html', '.'),
    ('HelpContent.md', '.'),
    ('WorkFlowTemplate.md', '.'),
]

hiddenimports += ['PIL._imaging', 'PIL._imagingft']

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='xAIPM_App',
    debug=False,
    strip=False,
    upx=True,
    console=True,   # 우선 True로 에러 확인, 정상 작동 확인 후 False로 변경
    icon=None,
)
