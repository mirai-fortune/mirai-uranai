/* ASUMIRA 占い — 鑑定ボタン テーマ別エフェクト
 * 対象セレクタ: .calc-btn, .trt-btn-draw
 * テーマ判定: html.theme-* クラス（localStorage "asumira-theme" と連動）
 */
(function () {
  'use strict';

  function getTheme() {
    var cl = document.documentElement.classList;
    if (cl.contains('theme-sakura'))    return 'sakura';
    if (cl.contains('theme-shinryoku')) return 'shinryoku';
    if (cl.contains('theme-minagi'))    return 'minagi';
    return 'gold';
  }

  /* ══════════════════════════════════════
     星空テーマ: 金色の星屑バースト
  ══════════════════════════════════════ */
  function GoldSpark(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 2.5 + Math.random() * 6.5;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd - Math.random() * 2.5;
    this.r   = 1.5 + Math.random() * 3.5;
    this.al  = 0.85 + Math.random() * 0.15;
    this.decay = 0.008 + Math.random() * 0.012;
    this.isStar = Math.random() < 0.45;
    this.pts = Math.random() < 0.5 ? 4 : 6;
    var t = Math.random();
    this.col = t < 0.5 ? [196, 168, 106] : t < 0.82 ? [255, 240, 190] : [232, 212, 160];
  }
  GoldSpark.prototype.update = function () {
    this.x  += this.vx;
    this.y  += this.vy;
    this.vy += 0.07;
    this.vx *= 0.97; this.vy *= 0.97;
    this.al -= this.decay;
    this.r  *= 0.988;
  };
  GoldSpark.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    ctx.shadowColor = 'rgba(255,240,160,0.8)';
    ctx.shadowBlur  = 9;
    var c = 'rgb(' + this.col.join(',') + ')';
    if (this.isStar) {
      ctx.translate(this.x, this.y);
      ctx.beginPath();
      for (var i = 0; i < this.pts * 2; i++) {
        var a  = (i / (this.pts * 2)) * Math.PI * 2 - Math.PI / 2;
        var ri = (i % 2 === 0) ? this.r : this.r * 0.42;
        if (i === 0) ctx.moveTo(Math.cos(a) * ri, Math.sin(a) * ri);
        else         ctx.lineTo(Math.cos(a) * ri, Math.sin(a) * ri);
      }
      ctx.closePath();
      ctx.fillStyle = c;
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = c;
      ctx.fill();
    }
    ctx.restore();
  };

  /* ══════════════════════════════════════
     桜花テーマ: 桜の花びらバースト
  ══════════════════════════════════════ */
  var SAKURA_C = [[255, 182, 205], [255, 160, 185], [240, 140, 170], [255, 205, 222]];
  function SakuraBurst(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 1.5 + Math.random() * 5.5;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd - (1.5 + Math.random() * 2.5);
    this.sA    = 6 + Math.random() * 7;
    this.sB    = this.sA * 0.55;
    this.rot   = Math.random() * Math.PI * 2;
    this.rotSp = (Math.random() - 0.5) * 0.08;
    this.sw    = Math.random() * Math.PI * 2;
    this.swSp  = 0.04 + Math.random() * 0.04;
    this.swR   = 1.2 + Math.random() * 2;
    this.al    = 0.9;
    this.decay = 0.006 + Math.random() * 0.007;
    this.col = SAKURA_C[Math.floor(Math.random() * SAKURA_C.length)];
  }
  SakuraBurst.prototype.update = function () {
    this.sw += this.swSp;
    this.x  += this.vx + Math.sin(this.sw) * this.swR * 0.3;
    this.y  += this.vy;
    this.vy += 0.04;
    this.vx *= 0.97;
    this.rot += this.rotSp;
    this.al  -= this.decay;
  };
  SakuraBurst.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rot);
    ctx.shadowColor = 'rgba(255,155,195,0.65)';
    ctx.shadowBlur  = 6;
    ctx.beginPath();
    ctx.ellipse(0, 0, this.sA, this.sB, 0, 0, Math.PI * 2);
    ctx.fillStyle = 'rgb(' + this.col.join(',') + ')';
    ctx.fill();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     蛍火テーマ: 蛍のバースト
  ══════════════════════════════════════ */
  var FF_C = [[180, 230, 80], [150, 220, 100], [200, 235, 60], [220, 255, 120]];
  function FireflyBurst(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 1 + Math.random() * 4.5;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd - (1 + Math.random() * 2.5);
    this.r   = 2 + Math.random() * 3.5;
    this.al  = 0.85 + Math.random() * 0.15;
    this.decay = 0.006 + Math.random() * 0.008;
    this.ph  = Math.random() * Math.PI * 2;
    this.bSp = 0.1 + Math.random() * 0.12;
    this.col = FF_C[Math.floor(Math.random() * FF_C.length)];
  }
  FireflyBurst.prototype.update = function () {
    this.x  += this.vx;
    this.y  += this.vy;
    this.vy -= 0.022;
    this.vx *= 0.97; this.vy *= 0.97;
    this.ph += this.bSp;
    this.al -= this.decay;
  };
  FireflyBurst.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    var br = Math.max(0.3, Math.sin(this.ph));
    var r = this.r, co = this.col;
    ctx.save();
    ctx.globalAlpha = this.al * br;
    var g = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, r * 4);
    g.addColorStop(0,   'rgba(' + co[0] + ',' + co[1] + ',' + co[2] + ',0.85)');
    g.addColorStop(0.4, 'rgba(' + co[0] + ',' + co[1] + ',' + co[2] + ',0.3)');
    g.addColorStop(1,   'rgba(' + co[0] + ',' + co[1] + ',' + co[2] + ',0)');
    ctx.beginPath();
    ctx.arc(this.x, this.y, r * 4, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.globalAlpha = this.al;
    ctx.shadowColor = 'rgba(200,255,100,0.85)';
    ctx.shadowBlur  = 10;
    ctx.beginPath();
    ctx.arc(this.x, this.y, r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,220,0.95)';
    ctx.fill();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     水凪テーマ: 水紋 + 水飛沫
  ══════════════════════════════════════ */
  function WaterRipple(cx, cy, delay) {
    this.x = cx; this.y = cy;
    this.r    = 0;
    this.maxR = 80 + Math.random() * 60;
    this.speed = 2.8 + Math.random() * 2;
    this.al   = 0.65;
    this.delay = delay || 0;
    this.hue  = 195 + Math.random() * 40;
  }
  WaterRipple.prototype.update = function () {
    if (this.delay > 0) { this.delay--; return; }
    this.r  += this.speed;
    this.al  = 0.6 * Math.max(0, 1 - this.r / this.maxR);
  };
  WaterRipple.prototype.draw = function (ctx) {
    if (this.delay > 0 || this.al <= 0) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.strokeStyle = 'hsla(' + this.hue + ',78%,72%,1)';
    ctx.lineWidth   = 1.8;
    ctx.shadowColor = 'hsla(' + this.hue + ',80%,78%,0.65)';
    ctx.shadowBlur  = 6;
    ctx.stroke();
    ctx.restore();
  };

  function WaterDrop(cx, cy) {
    var ang = Math.random() * Math.PI * 2;
    var spd = 2 + Math.random() * 5.5;
    this.x = cx; this.y = cy;
    this.vx = Math.cos(ang) * spd;
    this.vy = Math.sin(ang) * spd - (1 + Math.random() * 3);
    this.r   = 1.5 + Math.random() * 3;
    this.al  = 0.7 + Math.random() * 0.3;
    this.decay = 0.008 + Math.random() * 0.01;
    this.hue = 200 + Math.random() * 40;
  }
  WaterDrop.prototype.update = function () {
    this.x  += this.vx;
    this.y  += this.vy;
    this.vy += 0.13;
    this.vx *= 0.97;
    this.al -= this.decay;
  };
  WaterDrop.prototype.draw = function (ctx) {
    if (this.al <= 0) return;
    ctx.save();
    ctx.globalAlpha = this.al;
    var r = this.r;
    var g = ctx.createRadialGradient(this.x - r * 0.3, this.y - r * 0.3, 0, this.x, this.y, r);
    g.addColorStop(0,   'rgba(220,245,255,0.9)');
    g.addColorStop(0.6, 'hsla(' + this.hue + ',80%,70%,0.5)');
    g.addColorStop(1,   'hsla(' + this.hue + ',90%,60%,0)');
    ctx.shadowColor = 'hsla(' + this.hue + ',80%,82%,0.55)';
    ctx.shadowBlur  = 6;
    ctx.beginPath();
    ctx.arc(this.x, this.y, r, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.restore();
  };

  /* ══════════════════════════════════════
     パーティクル生成
  ══════════════════════════════════════ */
  function createParticles(theme, cx, cy) {
    var ps = [];
    var mobile = window.innerWidth < 768;
    var n = mobile ? 16 : 28;
    var i;
    if (theme === 'sakura') {
      for (i = 0; i < n; i++) ps.push(new SakuraBurst(cx, cy));
    } else if (theme === 'shinryoku') {
      for (i = 0; i < n; i++) ps.push(new FireflyBurst(cx, cy));
    } else if (theme === 'minagi') {
      ps.push(new WaterRipple(cx, cy, 0));
      ps.push(new WaterRipple(cx, cy, 10));
      ps.push(new WaterRipple(cx, cy, 20));
      var dn = mobile ? 13 : 22;
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
    var rect = btn.getBoundingClientRect();
    var cx = rect.left + rect.width  / 2;
    var cy = rect.top  + rect.height / 2;

    var canvas = document.createElement('canvas');
    canvas.style.cssText = [
      'position:fixed', 'top:0', 'left:0',
      'width:100vw', 'height:100vh',
      'z-index:9999', 'pointer-events:none',
      'transition:opacity 0.75s ease'
    ].join(';');
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);

    var ctx  = canvas.getContext('2d');
    var ps   = createParticles(getTheme(), cx, cy);
    var raf;

    setTimeout(function () { canvas.style.opacity = '0'; }, 1650);
    setTimeout(function () { cancelAnimationFrame(raf); canvas.remove(); }, 2400);

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
    var btns = document.querySelectorAll('.calc-btn, .trt-btn-draw');
    for (var i = 0; i < btns.length; i++) {
      (function (btn) {
        btn.addEventListener('click', function () { triggerEffect(btn); });
      })(btns[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attach);
  } else {
    attach();
  }
})();
