"""Build offline assets from pinned upstream sources and verified release artifacts."""
from pathlib import Path
import argparse,base64,hashlib,json,re,shutil,subprocess,sys,zipfile

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--cache',type=Path,default=ROOT/'build/cache')
parser.add_argument('--upstream',type=Path)
args=parser.parse_args()
cache=args.cache.resolve();cache.mkdir(parents=True,exist_ok=True)
versions=json.loads((ROOT/'runtime/versions.json').read_text())
upstream=args.upstream.resolve() if args.upstream else cache/'freecad-web'
if not upstream.exists():
    subprocess.run(['git','clone','--depth','1','--branch',versions['engine']['tag'],versions['engine']['repository'],str(upstream)],check=True)
tag=subprocess.check_output(['git','describe','--tags','--exact-match'],cwd=upstream,text=True).strip()
assert tag==versions['engine']['tag'], 'Use the pinned engine source tag'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip()==versions['engine']['commit'], 'Engine commit differs'
out=ROOT/'app/src/main/assets/engine';out.mkdir(parents=True,exist_ok=True)

def verified(url,name,sha):
    p=cache/name
    def digest():return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    if digest()!=sha:
        tmp=p.with_suffix(p.suffix+'.download')
        subprocess.run(['curl','-L','--fail','--retry','3','-o',str(tmp),url],check=True)
        assert hashlib.sha256(tmp.read_bytes()).hexdigest()==sha, 'Checksum mismatch: '+name
        tmp.replace(p)
    return p

for name,sha in versions['engine']['assets'].items():
    p=verified('https://github.com/Virtastic/freecad-web/releases/download/'+versions['engine']['tag']+'/'+name,name,sha)
    shutil.copy2(p,out/name)
subprocess.run([sys.executable,str(upstream/'tools/patch-freecad-js.py'),str(out/'FreeCAD.js')],check=True)
subprocess.run([sys.executable,str(upstream/'tools/patch-freecad-js.py'),str(out/'FreeCAD.js'),'--check'],check=True)
for name in ('qtloader.js','legal.html','icon-192.png','icon-512.png'):
    shutil.copy2(upstream/'play-gui'/name,out/name)
for name in ('LICENSE','NOTICE'):
    shutil.copy2(upstream/name,out/name)
shutil.copytree(upstream/'LICENSES',out/'LICENSES',dirs_exist_ok=True)
shutil.copytree(upstream/'play-gui/am',out/'am',dirs_exist_ok=True)
bootfile=out/'am/fcweb_am_boot.py'
boot=bootfile.read_text(encoding='utf-8')
boot=boot.replace('        fcweb_share.install()', '        pass  # Offline edition has no shared-session server')
boot=boot.replace('    state = {"timer": None, "tries": 0, "done": False}',
                  '    return  # Keep fonts/quantity/asyncio support; no online Addon Manager\n    state = {"timer": None, "tries": 0, "done": False}')
bootfile.write_text(boot,encoding='utf-8')
sharefile=out/'am/fcweb_share.py'
share=sharefile.read_text(encoding='utf-8')
assert share.count('def install():')==1
sharefile.write_text(share.replace('def install():','def install():\n    return  # No shared-session backend in the offline APK'),encoding='utf-8')

page=(upstream/'play-gui/freecad-gui.html').read_text(encoding='utf-8')
needle="const instance = window.fcInstance = await qtLoad(__cfg);"
assert page.count(needle)==1
page=page.replace(needle,"await window.fusionFlowPrepare(__cfg);\n     "+needle)
page=page.replace("FreeCAD.data.gz?v=1","FreeCAD.data")
page=page.replace('__FCWEB_BUILD__','FusionFlow-Android-0.1.0-alpha.1')
page=page.replace('</head>','<script src="android-bootstrap.js"></script></head>',1)
# This APK targets tablets. Keep the actual WASM, shared-memory and GPU probes.
assert page.count("if (isMobile()) return wall('mobile');")==1
page=page.replace("if (isMobile()) return wall('mobile');", "// Tablet support is capability-tested below.")
page=page.replace('for _d in Gui.listDocuments():','for _d in App.listDocuments():')
# The APK already contains the engine; duplicate 500 MB of Cache Storage is wasteful.
page=page.replace("async function __engineCache(){ try { return await caches.open(ENGINE_CACHE); } catch(e){ return null; } }",
                  "async function __engineCache(){ return null; }")
page=page.replace("if ('serviceWorker' in navigator &&", "if (false && 'serviceWorker' in navigator &&")
page=page.replace("first load downloads about 115 MB", "Offline edition · FusionFlow included")
page=re.sub(r'<p class="ld-lede">.*?</p>',
            '<p class="ld-lede">FreeCAD 1.1.3 with FusionFlow. The CAD engine runs locally on this device. First startup can take over a minute.</p>',page,count=1,flags=re.S)
page=page.replace("__setBoot('Downloading… ' + pct + '%');", "__setBoot('Loading bundled engine… ' + pct + '%');")
# Suppress browser-install/backup-folder offers: Android uses its system file picker.
page=page.replace("window.__fcWorkSaved = function () {", "window.__fcWorkSaved = function () { return;")
page=page.replace("window.fcwebWarnEvictable = function () {", "window.fcwebWarnEvictable = function () { return;")
# Remove anonymous counters from our build, not merely their network destination.
start=page.index('window.fcwebEvent = function (name, kind, ms) {')
end=page.index("window.fcwebEvent('boot_start');",start)
page=page[:start]+'window.fcwebEvent = function () {};\n'+page[end:]
(out/'freecad-gui.html').write_text(page,encoding='utf-8')
shutil.copy2(ROOT/'runtime/android-bootstrap.js',out/'android-bootstrap.js')
addon=versions['fusionflow']
archive=verified(addon['url'],'FusionFlow-addon.zip',addon['sha256'])
files={}
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        rel=Path(name).relative_to('FusionFlow-addon')
        if '..' in rel.parts:raise ValueError('Unsafe archive path')
        if rel.parts[0]=='FusionFlow':target=rel
        elif rel.parts[:2] in [('vendor','freecad-fusion'),('vendor','OpenTheme')]:target=Path(*rel.parts[1:])
        else:continue
        if name.endswith('/') or rel.name.startswith('test_'):continue
        data=z.read(name)
        if target.as_posix() in ('freecad-fusion/InitGui.py','FusionFlow/InitGui.py'):
            data=b'# Android bootstrap registers navigation after the CAD workbench is ready.\n'
        files['/fusionflow/'+target.as_posix()]=base64.b64encode(data).decode('ascii')
files['/fusionflow/start.py']=base64.b64encode((ROOT/'runtime/start.py').read_bytes()).decode('ascii')
(out/'fusionflow-files.json').write_text(json.dumps(files,separators=(',',':')),encoding='utf-8')
for name in ('LICENSE','NOTICE.md'):
    shutil.copy2(ROOT/name,out/('ANDROID-'+name))
shutil.copy2(ROOT/'runtime/versions.json',out/'versions.json')
print('Offline engine prepared:',out)
