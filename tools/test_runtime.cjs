// SPDX-License-Identifier: GPL-3.0-only
// npm install --no-save playwright, then node tools/test_runtime.cjs <CDP endpoint>
// Connect only to a dedicated debug APK/emulator: this creates a synthetic model.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..'),out=path.join(root,'build','qa');
fs.mkdirSync(out,{recursive:true});
(async()=>{
  const browser=await chromium.connectOverCDP(process.argv[2]||'http://127.0.0.1:9224');
  const page=browser.contexts()[0].pages().find(p=>p.url().includes('freecad-gui.html'));
  assert(page,'The packaged CAD page is not open');
  await page.waitForFunction(()=>{try{return window.__fcWorkReady && !window.__fcPyBusy && !!window.fcInstance.FS.stat('/fusionflow-ready.json')}catch{return false}},{},{timeout:180000});
  const boot=await page.evaluate(()=>JSON.parse(new TextDecoder().decode(fcInstance.FS.readFile('/fusionflow-ready.json'))));
  assert(boot.ready,JSON.stringify(boot));
  const source=fs.readFileSync(path.join(root,'tests','model_smoke.py'),'utf8');
  await page.evaluate(code=>{try{fcInstance.FS.unlink('/fusionflow-smoke.json')}catch{};__fcRunPyGuarded(code)},source);
  await page.waitForFunction(()=>{try{return !!fcInstance.FS.stat('/fusionflow-smoke.json')}catch{return false}},{},{timeout:180000});
  const result=await page.evaluate(()=>JSON.parse(new TextDecoder().decode(fcInstance.FS.readFile('/fusionflow-smoke.json'))));
  result.environment=await page.evaluate(()=>({userAgent:navigator.userAgent,crossOriginIsolated,JSPI:typeof WebAssembly.Suspending}));
  fs.writeFileSync(path.join(out,'model-smoke.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
  await page.waitForTimeout(2000);
  await page.screenshot({path:path.join(out,'model-smoke.png')});
  assert(result.pass,result.error);
  process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
