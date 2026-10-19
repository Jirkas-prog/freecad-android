// SPDX-License-Identifier: GPL-3.0-only
// Installed before the upstream loader. Never fetches a remote modelling service.
window.fusionFlowFiles = fetch('fusionflow-files.json').then(r => {
  if (!r.ok) throw new Error('The bundled FusionFlow files are missing');
  return r.json();
});
window.fusionFlowPrepare = async function (cfg) {
  const files = await window.fusionFlowFiles;
  cfg.preRun.push(function () {
    for (const [name, data] of Object.entries(files)) {
      if (!name.startsWith('/fusionflow/') || name.includes('..')) throw new Error('Invalid bundled path');
      cfg.FS.mkdirTree(name.slice(0, name.lastIndexOf('/')));
      cfg.FS.writeFile(name, Uint8Array.from(atob(data), c => c.charCodeAt(0)));
    }
  });
};

// Reuse the upstream interpreter gate: CPython must never be entered during JSPI suspension.
const fusionFlowStart = setInterval(() => {
  const m = window.fcInstance;
  if (!window.__fcWorkReady || !window.__fcRunPyGuarded || window.__fcPyBusy || !m?.FS) return;
  clearInterval(fusionFlowStart);
  const code = new TextDecoder().decode(m.FS.readFile('/fusionflow/start.py'));
  window.__fcRunPyGuarded(code);
}, 750);

// WebView does not download blob: URLs itself. Send small chunks to Android's
// Storage Access Framework; the user chooses the destination and can cancel.
const nativeClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () {
  if (window.FusionFlowAndroid && this.href.startsWith('blob:')) {
    const link=this;
    (async () => {
      const blob=await fetch(link.href).then(r=>r.blob());
      if(!FusionFlowAndroid.begin(link.download || 'Model.FCStd')) throw new Error('Another export is still pending');
      try {
        for(let offset=0;offset<blob.size;offset+=65536) {
          const bytes=new Uint8Array(await blob.slice(offset,offset+65536).arrayBuffer());
          let text=''; for(const byte of bytes)text+=String.fromCharCode(byte);
          if(!FusionFlowAndroid.chunk(btoa(text)))throw new Error('The file could not be transferred');
        }
        FusionFlowAndroid.finish();
      } catch(e) {FusionFlowAndroid.cancel();throw e;}
    })().catch(e=>window.fcwebNotify?.('Export failed: '+e.message,'error'));
    return;
  }
  return nativeClick.call(this);
};
