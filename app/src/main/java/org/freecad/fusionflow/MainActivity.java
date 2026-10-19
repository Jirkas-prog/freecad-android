// SPDX-License-Identifier: GPL-3.0-only
package org.freecad.fusionflow;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.view.WindowInsets;
import android.util.Base64;
import android.webkit.*;
import android.widget.*;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;
import java.io.*;
import java.util.*;

/** Offline host for the FreeCAD WebAssembly runtime. Only packaged content can execute. */
public final class MainActivity extends Activity {
    static final String ORIGIN = "https://appassets.androidplatform.net";
    private WebView view;
    private ValueCallback<Uri[]> fileCallback;
    private File exportFile;
    private FileOutputStream exportStream;
    private long exportBytes;
    private String exportName;
    private volatile boolean exportPending;
    private final ExportBridge exportBridge=new ExportBridge();
    private final static int OPEN = 1, SAVE = 2;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        view = new WebView(this);
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);
        view.setBackgroundColor(0xff303641);
        view.getSettings().setJavaScriptEnabled(true);
        view.getSettings().setDomStorageEnabled(true);
        view.getSettings().setAllowFileAccess(false);
        view.getSettings().setAllowContentAccess(true);
        view.getSettings().setSupportMultipleWindows(false);
        view.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        view.getSettings().setBuiltInZoomControls(false);
        view.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                Uri u=r.getUrl();
                if (!"https".equals(u.getScheme()) || !"appassets.androidplatform.net".equals(u.getHost()) || !"GET".equals(r.getMethod()))
                    return response(403,"Forbidden","text/plain",new ByteArrayInputStream(new byte[0]));
                String path=u.getPath();
                if (path==null || path.contains("..") || path.contains("\\"))
                    return response(400,"Bad Request","text/plain",new ByteArrayInputStream(new byte[0]));
                if (path.equals("/")) path="/freecad-gui.html";
                String mime=path.endsWith(".wasm")?"application/wasm":path.endsWith(".js")?"text/javascript":
                    path.endsWith(".html")?"text/html":path.endsWith(".json")?"application/json":
                    path.endsWith(".svg")?"image/svg+xml":path.endsWith(".png")?"image/png":"application/octet-stream";
                try { return response(200,"OK",mime,getAssets().open("engine"+path)); }
                catch(IOException e) { return response(404,"Not Found","text/plain",new ByteArrayInputStream(new byte[0])); }
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                return !r.getUrl().toString().startsWith(ORIGIN+"/");
            }
            @Override public boolean onRenderProcessGone(WebView v, RenderProcessGoneDetail detail) {
                v.destroy();
                view=null;
                showMessage("FreeCAD stopped", "The graphics process stopped. Reopen the app to recover locally saved work if available. Export important work to a document file regularly.");
                return true;
            }
        });
        view.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView w, ValueCallback<Uri[]> callback, FileChooserParams p) {
                if(fileCallback!=null) fileCallback.onReceiveValue(null);
                fileCallback=callback;
                Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");
                i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,p.getMode()==FileChooserParams.MODE_OPEN_MULTIPLE);
                startActivityForResult(i,OPEN);return true;
            }
            @Override public boolean onConsoleMessage(ConsoleMessage message) {
                if(BuildConfig.DEBUG) android.util.Log.d("FusionFlow",message.message());
                return true;
            }
        });
        view.addJavascriptInterface(exportBridge,"FusionFlowAndroid");
        FrameLayout frame=new FrameLayout(this);
        frame.setBackgroundColor(0xff303641);
        frame.addView(view,new FrameLayout.LayoutParams(-1,-1));
        frame.setOnApplyWindowInsetsListener((v,insets)->{
            if(Build.VERSION.SDK_INT>=30) {
                android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                v.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            } else {
                v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        setContentView(frame);
        if(WebViewFeature.isFeatureSupported(WebViewFeature.MULTI_PROFILE)
                && WebViewFeature.isFeatureSupported(WebViewFeature.CROSS_ORIGIN_ISOLATED_ALLOWLIST)) {
            // Admit only our packaged origin; request handling and CSP reject remote code.
            WebViewCompat.getProfile(view).setCrossOriginIsolatedAllowlist(Collections.singleton(ORIGIN));
            view.loadUrl(ORIGIN+"/freecad-gui.html");
        } else {
            showMessage("WebView update required", "This FreeCAD runtime needs a newer Android System WebView with cross-origin isolated allowlist support. The installed provider cannot run it. No CAD document has been changed.");
        }
    }

    private WebResourceResponse response(int status,String reason,String type,InputStream input) {
        Map<String,String> headers=new HashMap<>();
        headers.put("Cross-Origin-Opener-Policy","same-origin");
        headers.put("Cross-Origin-Embedder-Policy","require-corp");
        headers.put("Document-Isolation-Policy","isolate-and-require-corp");
        headers.put("Cross-Origin-Resource-Policy","same-origin");
        headers.put("X-Content-Type-Options","nosniff");
        headers.put("Content-Security-Policy","default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' blob:; frame-src 'none'; object-src 'none'; base-uri 'none'");
        return new WebResourceResponse(type,"UTF-8",status,reason,headers,input);
    }
    private void showMessage(String title,String body) {
        runOnUiThread(()->new AlertDialog.Builder(this).setTitle(title).setMessage(body).setPositiveButton("OK",null).show());
    }

    /** Chunked transfer avoids putting an entire CAD file in a Binder message. */
    final class ExportBridge {
        @JavascriptInterface public synchronized boolean begin(String name) {
            if(exportPending || exportStream!=null) return false;
            try {
                exportFile=File.createTempFile("export-",".tmp",getCacheDir());
                exportStream=new FileOutputStream(exportFile);exportBytes=0;
                exportName=new File(name.replace('\\','/')).getName();
                if(exportName.isEmpty())exportName="Model.FCStd";
                return true;
            } catch(IOException e) { cancel();showMessage("Export failed",e.getMessage());return false; }
        }
        @JavascriptInterface public synchronized boolean chunk(String data) {
            if(exportStream==null || data.length()>100000) return false;
            try {
                byte[] bytes=Base64.decode(data,Base64.DEFAULT);
                if(exportBytes+bytes.length>512L*1024*1024)throw new IOException("The file exceeds the 512 MB export limit.");
                exportStream.write(bytes);exportBytes+=bytes.length;return true;
            } catch(Exception e) { cancel();showMessage("Export failed",e.getMessage());return false; }
        }
        @JavascriptInterface public synchronized void cancel() {
            if(exportPending)return;
            try { if(exportStream!=null)exportStream.close(); } catch(IOException ignored){}
            exportStream=null;
            if(exportFile!=null)exportFile.delete();
            exportFile=null;
        }
        @JavascriptInterface public synchronized void finish() {
            if(exportStream==null)return;
            try { exportStream.close();exportStream=null;exportPending=true;
                runOnUiThread(()->startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT)
                    .addCategory(Intent.CATEGORY_OPENABLE).setType("application/octet-stream")
                    .putExtra(Intent.EXTRA_TITLE,exportName),SAVE));
            } catch(IOException e) { cancel();showMessage("Export failed",e.getMessage()); }
        }
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request==OPEN && fileCallback!=null) {
            fileCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result,data));fileCallback=null;
        }
        if(request==SAVE) {
            if(result==RESULT_OK && data!=null && exportFile!=null) {
                Uri destination=data.getData();File source=exportFile;
                new Thread(()->{
                    try(InputStream in=new FileInputStream(source);OutputStream out=getContentResolver().openOutputStream(destination,"wt")) {
                        if(out==null)throw new IOException("The selected document could not be opened.");
                        byte[] block=new byte[65536];int n;while((n=in.read(block))!=-1)out.write(block,0,n);
                        runOnUiThread(()->Toast.makeText(this,"File saved",Toast.LENGTH_SHORT).show());
                    } catch(IOException e) { showMessage("Export failed","The model is still in the CAD session. "+e.getMessage()); }
                    finally { source.delete();exportFile=null;exportPending=false; }
                },"CAD-export").start();
            } else { if(exportFile!=null)exportFile.delete();exportFile=null;exportPending=false; }
        }
    }
    @Override public void onBackPressed() {
        new AlertDialog.Builder(this).setTitle("Close FreeCAD?")
            .setMessage("Export important work before closing. The app also keeps local session recovery.")
            .setNegativeButton("Keep working",null).setPositiveButton("Close",(d,w)->finish()).show();
    }
    @Override protected void onDestroy() {
        exportBridge.cancel();
        if(view!=null)view.destroy();
        if(fileCallback!=null)fileCallback.onReceiveValue(null);
        super.onDestroy();
    }
}
