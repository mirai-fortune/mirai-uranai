/* ASUMIRA 占い — 鑑定ボタン テーマ別エフェクト v2
 * 対象セレクタ: .calc-btn, .trt-btn-draw
 * テーマ判定: html.theme-* クラス（localStorage "asumira-theme" と連動）
 */
(function () {
  'use strict';

  /* テーマカラー設定 */
  var TC = {
    gold:      { ring: 'rgba(196,168,106,', flash: 'rgba(255,248,200,' },
    sakura:    { ring: 'rgba(255,155,190,', flash: 'rgba(255,218,235,' },
    shinryoku: { ring: 'rgba(130,220,80,',  flash: 'rgba(200,255,160,' },
    minagi:    { ring: 'rgba(80,170,230,',  flash: 'rgba(185,230,255,' }
  };

  function getTheme() {
    var cl = document.documentElement.classList;
    if (cl.contains('theme-sakura'))    return 'sakura';
    if (cl.contains('theme-shinryoku')) return 'shinryoku';
    if (cl.contains('theme-minagi'))    return 'minagi';
    return 'gold';
  }

  /* ══════════════════════════════════════
     共通: 中心フラッシュ（全テーマ）
     ボタン位置に明確な視覚的起点を作る
  ══════════════════════════════════════ */
  function FlashCenter(cx, cy, theme) {
    this.x = cx; this.y = cy;
    this.r  = 10;
    this.al = 1.0;
    this.fc = TC[theme].flash;
  }
  FlashCenter.prototype.update = function () {
    this.r  *= 1.18;
    this.al *= 0.78;
  };
  FlashCenter.prototype.draw = function (ctx) {
    if (this.al < 0.015) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    var g = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.r);
    g.addColorStop(0,   this.fc + '1)');
    g.addColorStop(0.35, this.fc + '0.55)');
    g.addColorStop(1,   this.fc + '0)');
    ctx.beginPath(); ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fillStyle = g; ctx.fill();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     共通: 拡張リング（全テーマ）
     起点から広がる同心円で「ここから出た」を強調
  ══════════════════════════════════════ */
  function Ring(cx, cy, theme, delay) {
    this.x = cx; this.y = cy;
    this.r     = 6;
    this.al    = 0.85;
    this.delay = delay || 0;
    this.rc    = TC[theme].ring;
    this.lw    = 2.2;
  }
  Ring.prototype.update = function () {
    if (this.delay > 0) { this.delay--; return; }
    this.r  += 5.5;
    this.al *= 0.91;
    this.lw *= 0.97;
  };
  Ring.prototype.draw = function (ctx) {
    if (this.delay > 0 || this.al < 0.015) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    ctx.beginPath(); ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.strokeStyle = this.rc + '1)';
    ctx.lineWidth   = this.lw;
    ctx.shadowColor = this.rc + '0.65)';
    ctx.shadowBlur  = 10;
    ctx.stroke();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     星空テーマ: 金色の星屑バースト
     純放射状バースト、一部が星形
  ══════════════════════════════════════ */
  function GoldSpark(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 2.5 + Math.random() * 7.5;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd;          /* バイアスなし・純放射 */
    this.r      = 1.8 + Math.random() * 3.8;
    this.al     = 0.85 + Math.random() * 0.15;
    this.decay  = 0.007 + Math.random() * 0.011;
    this.isStar = Math.random() < 0.48;
    this.pts    = Math.random() < 0.55 ? 4 : 6;
    var t = Math.random();
    this.col = t < 0.5 ? [196,168,106] : t < 0.82 ? [255,242,195] : [232,215,162];
  }
  GoldSpark.prototype.update = function () {
    this.x  += this.vx;
    this.y  += this.vy;
    this.vy += 0.055;                        /* 弱めの重力 */
    this.vx *= 0.97; this.vy *= 0.97;
    this.al -= this.decay;
    this.r  *= 0.990;
  };
  GoldSpark.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    ctx.shadowColor = 'rgba(255,240,155,0.9)';
    ctx.shadowBlur  = 10;
    var c = 'rgb(' + this.col.join(',') + ')';
    if (this.isStar) {
      ctx.translate(this.x, this.y);
      ctx.beginPath();
      for (var i = 0; i < this.pts * 2; i++) {
        var a  = (i / (this.pts * 2)) * Math.PI * 2 - Math.PI / 2;
        var ri = (i % 2 === 0) ? this.r : this.r * 0.42;
        if (i === 0) ctx.moveTo(Math.cos(a)*ri, Math.sin(a)*ri);
        else         ctx.lineTo(Math.cos(a)*ri, Math.sin(a)*ri);
      }
      ctx.closePath(); ctx.fillStyle = c; ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = c; ctx.fill();
    }
    ctx.restore();
  };

  /* ══════════════════════════════════════
     桜花テーマ: 桜の花びらバースト
     初期は放射状バースト、その後重力と風でゆらゆら漂う
  ══════════════════════════════════════ */
  var SAKURA_C = [[255,182,205],[255,160,185],[242,142,172],[255,208,224]];
  function SakuraBurst(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 2 + Math.random() * 5.5;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd;          /* 純放射 */
    this.sA    = 6 + Math.random() * 7;
    this.sB    = this.sA * 0.55;
    this.rot   = Math.random() * Math.PI * 2;
    this.rotSp = (Math.random() - 0.5) * 0.09;
    this.sw    = Math.random() * Math.PI * 2;
    this.swSp  = 0.035 + Math.random() * 0.04;
    this.swR   = 1.0 + Math.random() * 1.8;
    this.al    = 0.92;
    this.decay = 0.0055 + Math.random() * 0.007;
    this.col   = SAKURA_C[Math.floor(Math.random() * SAKURA_C.length)];
  }
  SakuraBurst.prototype.update = function () {
    this.sw += this.swSp;
    this.x  += this.vx + Math.sin(this.sw) * this.swR * 0.28;
    this.y  += this.vy;
    this.vy += 0.032;                        /* 弱めの重力（自然な落下） */
    this.vx *= 0.972;
    this.rot += this.rotSp;
    this.al  -= this.decay;
  };
  SakuraBurst.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    ctx.translate(this.x, this.y); ctx.rotate(this.rot);
    ctx.shadowColor = 'rgba(255,150,190,0.7)';
    ctx.shadowBlur  = 7;
    ctx.beginPath();
    ctx.ellipse(0, 0, this.sA, this.sB, 0, 0, Math.PI * 2);
    ctx.fillStyle = 'rgb(' + this.col.join(',') + ')';
    ctx.fill();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     蛍火テーマ: 蛍バースト
     放射状に飛び出した後、自然に上方へ漂う
  ══════════════════════════════════════ */
  var FF_C = [[175,228,75],[145,218,95],[196,232,55],[215,252,115]];
  function FireflyBurst(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 1.2 + Math.random() * 4.5;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd;          /* 純放射 */
    this.r     = 2.2 + Math.random() * 3.5;
    this.al    = 0.85 + Math.random() * 0.15;
    this.decay = 0.0058 + Math.random() * 0.008;
    this.ph    = Math.random() * Math.PI * 2;
    this.bSp   = 0.08 + Math.random() * 0.11;
    this.col   = FF_C[Math.floor(Math.random() * FF_C.length)];
  }
  FireflyBurst.prototype.update = function () {
    this.x  += this.vx;
    this.y  += this.vy;
    this.vy -= 0.025;                        /* 蛍らしい上昇傾向（自然な浮力） */
    this.vx *= 0.97; this.vy *= 0.97;
    this.ph += this.bSp;
    this.al -= this.decay;
  };
  FireflyBurst.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    var br = Math.max(0.28, Math.sin(this.ph));
    var r = this.r, co = this.col;
    ctx.save();
    /* 光の輪 */
    ctx.globalAlpha = this.al * br * 0.75;
    var g = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, r * 4.5);
    g.addColorStop(0,   'rgba(' + co[0] + ',' + co[1] + ',' + co[2] + ',0.88)');
    g.addColorStop(0.4, 'rgba(' + co[0] + ',' + co[1] + ',' + co[2] + ',0.28)');
    g.addColorStop(1,   'rgba(' + co[0] + ',' + co[1] + ',' + co[2] + ',0)');
    ctx.beginPath(); ctx.arc(this.x, this.y, r * 4.5, 0, Math.PI * 2);
    ctx.fillStyle = g; ctx.fill();
    /* 光点 */
    ctx.globalAlpha = this.al;
    ctx.shadowColor = 'rgba(195,255,95,0.9)';
    ctx.shadowBlur  = 12;
    ctx.beginPath(); ctx.arc(this.x, this.y, r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,215,0.97)'; ctx.fill();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     水凪テーマ: 水紋 + 水飛沫
  ══════════════════════════════════════ */
  function WaterRipple(cx, cy, delay) {
    this.x = cx; this.y = cy;
    this.r     = 0;
    this.maxR  = 88 + Math.random() * 55;
    this.speed = 3.0 + Math.random() * 2;
    this.al    = 0.68;
    this.delay = delay || 0;
    this.hue   = 196 + Math.random() * 38;
  }
  WaterRipple.prototype.update = function () {
    if (this.delay > 0) { this.delay--; return; }
    this.r  += this.speed;
    this.al  = 0.62 * Math.max(0, 1 - this.r / this.maxR);
  };
  WaterRipple.prototype.draw = function (ctx) {
    if (this.delay > 0 || this.al <= 0) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    ctx.beginPath(); ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.strokeStyle = 'hsla(' + this.hue + ',78%,72%,1)';
    ctx.lineWidth   = 2.0;
    ctx.shadowColor = 'hsla(' + this.hue + ',80%,80%,0.7)';
    ctx.shadowBlur  = 7;
    ctx.stroke();
    ctx.restore();
  };

  function WaterDrop(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 2 + Math.random() * 6;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd;          /* 純放射 */
    this.r     = 1.5 + Math.random() * 3.2;
    this.al    = 0.72 + Math.random() * 0.28;
    this.decay = 0.008 + Math.random() * 0.01;
    this.hue   = 200 + Math.random() * 40;
  }
  WaterDrop.prototype.update = function () {
    this.x  += this.vx;
    this.y  += this.vy;
    this.vy += 0.14;                         /* 重力 */
    this.vx *= 0.97;
    this.al -= this.decay;
  };
  WaterDrop.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    ctx.save(); ctx.globalAlpha = this.al;
    var r = this.r;
    var g = ctx.createRadialGradient(this.x - r*0.3, this.y - r*0.3, 0, this.x, this.y, r);
    g.addColorStop(0,   'rgba(228,248,255,0.92)');
    g.addColorStop(0.6, 'hsla(' + this.hue + ',80%,70%,0.48)');
    g.addColorStop(1,   'hsla(' + this.hue + ',88%,62%,0)');
    ctx.shadowColor = 'hsla(' + this.hue + ',80%,84%,0.58)';
    ctx.shadowBlur  = 7;
    ctx.beginPath(); ctx.arc(this.x, this.y, r, 0, Math.PI * 2);
    ctx.fillStyle = g; ctx.fill();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     パーティクル生成
  ══════════════════════════════════════ */
  function createParticles(theme, cx, cy) {
    var ps = [];
    var mobile = window.innerWidth < 768;
    var i;

    /* 全テーマ共通: 中心フラッシュ + 3段リング */
    ps.push(new FlashCenter(cx, cy, theme));
    ps.push(new Ring(cx, cy, theme, 0));
    ps.push(new Ring(cx, cy, theme, 7));
    ps.push(new Ring(cx, cy, theme, 15));

    var n = mobile ? 18 : 42;

    if (theme === 'sakura') {
      for (i = 0; i < n; i++) ps.push(new SakuraBurst(cx, cy));
    } else if (theme === 'shinryoku') {
      for (i = 0; i < n; i++) ps.push(new FireflyBurst(cx, cy));
    } else if (theme === 'minagi') {
      ps.push(new WaterRipple(cx, cy, 0));
      ps.push(new WaterRipple(cx, cy, 11));
      ps.push(new WaterRipple(cx, cy, 24));
      var dn = mobile ? 14 : 28;
      for (i = 0; i < dn; i++) ps.push(new WaterDrop(cx, cy));
    } else {
      for (i = 0; i < n; i++) ps.push(new GoldSpark(cx, cy));
    }
    return ps;
  }

  /* ══════════════════════════════════════
     エフェクト起動
  ══════════════════════════════════════ */
  function triggerEffect(btn) {
    /* ボタン位置をビューポート座標で取得 */
    var rect = btn.getBoundingClientRect();
    var cx = rect.left + rect.width  / 2;
    var cy = rect.top  + rect.height / 2;
    var theme = getTheme();

    /* ボタン自体に瞬間フラッシュ */
    var themeGlow = {
      gold:      '0 0 18px 4px rgba(196,168,106,0.75)',
      sakura:    '0 0 18px 4px rgba(255,155,190,0.75)',
      shinryoku: '0 0 18px 4px rgba(130,220,80,0.75)',
      minagi:    '0 0 18px 4px rgba(80,170,230,0.75)'
    };
    var origBoxShadow  = btn.style.boxShadow;
    var origTransform  = btn.style.transform;
    var origTransition = btn.style.transition;
    btn.style.transition = 'transform 0.07s ease, box-shadow 0.28s ease';
    btn.style.transform  = 'scale(0.96)';
    btn.style.boxShadow  = themeGlow[theme];
    setTimeout(function () {
      btn.style.transform = origTransform;
      btn.style.boxShadow = origBoxShadow;
      setTimeout(function () { btn.style.transition = origTransition; }, 300);
    }, 70);

    /* エフェクト用 Canvas を生成 */
    var canvas = document.createElement('canvas');
    canvas.style.cssText = [
      'position:fixed', 'top:0', 'left:0',
      'width:100vw', 'height:100vh',
      'z-index:9999', 'pointer-events:none',
      'transition:opacity 0.65s ease'
    ].join(';');
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    var ps  = createParticles(theme, cx, cy);
    var raf;

    setTimeout(function () { canvas.style.opacity = '0'; }, 750);
    setTimeout(function () { cancelAnimationFrame(raf); canvas.remove(); }, 1400);

    function loop() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (var i = 0; i < ps.length; i++) {
        ps[i].update();
        ps[i].draw(ctx);
      }
      raf = requestAnimationFrame(loop);
    }
    raf = requestAnimationFrame(loop);
  }

  /* ══════════════════════════════════════
     ボタンにイベント付与
  ══════════════════════════════════════ */
  function attach() {
    var i;

    /*
     * .calc-btn: onclick属性をインターセプトして「エフェクト先行・計算遅延」方式に変更。
     *
     * 理由: onclick="calcIndividual()" が即座に scrollIntoView() を呼ぶため、
     *       固定canvasのエフェクトがスクロール中に画面に貼り付いて見えてしまう。
     *
     * 対策: onclickを外し、クリック時はエフェクトのみ起動。
     *       300ms後（フラッシュ+リングのインパクトが完了するタイミング）に
     *       元の処理を遅延実行する。
     *       パーティクルはスクロール中もフェード中のため視覚的に問題なし。
     */
    var calcBtns = document.querySelectorAll('.calc-btn');
    for (i = 0; i < calcBtns.length; i++) {
      (function (btn) {
        var original = btn.onclick;
        if (original) {
          btn.onclick = null;
          btn.addEventListener('click', function () {
            triggerEffect(btn);
            setTimeout(function () { original.call(btn); }, 300);
          });
        } else {
          btn.addEventListener('click', function () { triggerEffect(btn); });
        }
      })(calcBtns[i]);
    }

    /*
     * .trt-btn-draw: タロットは既存 addEventListener を維持。
     *                エフェクトのみ追加（スクロール挙動が異なるため遅延なし）。
     */
    var drawBtns = document.querySelectorAll('.trt-btn-draw');
    for (i = 0; i < drawBtns.length; i++) {
      (function (btn) {
        btn.addEventListener('click', function () { triggerEffect(btn); });
      })(drawBtns[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attach);
  } else {
    attach();
  }
})();
