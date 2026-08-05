/* ── ASUMIRA サイト一時非公開ゲート ──
   コードを変更したい場合は、新しいコードのSHA-256ハッシュ値を計算して
   ACCESS_CODE_HASH を書き換えてください。PowerShellで計算する例：

   $code = "新しいコード"
   $sha256 = [System.Security.Cryptography.SHA256]::Create()
   $bytes = [System.Text.Encoding]::UTF8.GetBytes($code)
   -join ($sha256.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") })

   このゲートを完全に外したい場合は、各HTMLファイルの
   <script src="/js/site-gate.js"></script> の行を削除してください。
*/
(function(){
  'use strict';
  var LS_KEY='asumira_site_unlocked';
  if(localStorage.getItem(LS_KEY)==='1')return;

  var ACCESS_CODE_HASH='e60d00a736ffae53efb15380ab2b5a20c0237185a6e4d375e9788748170cb5af';

  document.documentElement.style.visibility='hidden';

  function sha256Hex(str){
    var enc=new TextEncoder().encode(str);
    return crypto.subtle.digest('SHA-256',enc).then(function(buf){
      return Array.from(new Uint8Array(buf)).map(function(b){return b.toString(16).padStart(2,'0');}).join('');
    });
  }

  function showGate(){
    document.documentElement.style.visibility='visible';
    var overlay=document.createElement('div');
    overlay.id='site-gate-overlay';
    overlay.style.cssText='position:fixed;inset:0;background:#0a0906;color:#f5f2eb;z-index:2147483647;display:flex;align-items:center;justify-content:center;font-family:"Noto Sans JP",sans-serif;padding:20px;box-sizing:border-box;';
    overlay.innerHTML=
      '<div style="max-width:320px;width:100%;text-align:center;">'
      +'<p style="letter-spacing:.2em;font-size:12px;color:#c4a86a;margin-bottom:18px;">ASUMIRA 占い</p>'
      +'<p style="font-size:14px;margin-bottom:22px;line-height:1.9;">現在サイトは一時的に非公開にしております。<br>アクセスコードをご存知の方はご入力ください。</p>'
      +'<input id="site-gate-input" type="password" autocomplete="off" style="width:100%;padding:11px;font-size:16px;text-align:center;border:1px solid #c4a86a;background:transparent;color:#f5f2eb;margin-bottom:12px;box-sizing:border-box;border-radius:4px;">'
      +'<button id="site-gate-btn" style="width:100%;padding:11px;background:#c4a86a;color:#0a0906;border:none;cursor:pointer;font-size:14px;letter-spacing:.1em;border-radius:4px;">入る</button>'
      +'<p id="site-gate-err" style="color:#c97878;font-size:12px;margin-top:14px;visibility:hidden;">コードが違います</p>'
      +'</div>';
    document.body.appendChild(overlay);
    var prevOverflow=document.body.style.overflow;
    document.body.style.overflow='hidden';

    function tryUnlock(){
      var val=document.getElementById('site-gate-input').value;
      sha256Hex(val).then(function(hash){
        if(hash===ACCESS_CODE_HASH){
          localStorage.setItem(LS_KEY,'1');
          overlay.remove();
          document.body.style.overflow=prevOverflow;
        }else{
          document.getElementById('site-gate-err').style.visibility='visible';
        }
      });
    }
    document.getElementById('site-gate-btn').addEventListener('click',tryUnlock);
    document.getElementById('site-gate-input').addEventListener('keydown',function(e){if(e.key==='Enter')tryUnlock();});
    document.getElementById('site-gate-input').focus();
  }

  if(document.body){
    showGate();
  }else{
    document.addEventListener('DOMContentLoaded',showGate);
  }
})();
