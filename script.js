/* =========================================================================
   こま名刺ページ  —  設定はこのブロックだけ書き換えれば OK
   ========================================================================= */

/** リンク欄に並ぶボタン。url を実際のリンクに書き換えてください。
 *  不要なものは行ごと削除、増やしたい場合は同じ形で追記できます。
 *  size: "icon"    … アイコンだけの丸ボタン。連続するものは横一列に並ぶ
 *        "compact" … 横いっぱいで背の低い行
 *        省略      … 横いっぱいの標準の行（sub を付けると 2 行になる）
 *  title はアイコンだけの場合も必要（読み上げと補助表示に使う） */
const LINKS = [
  {
    title: "Instagram",
    url: "https://www.instagram.com/coma__days",
    icon: "instagram",
    accent: "linear-gradient(135deg,#f9ce34,#ee2a7b 48%,#6228d7)",
    size: "icon",
  },
  {
    title: "TikTok",
    url: "https://www.tiktok.com/t/ZS9hNdhbGU23o-cHRxk/",
    icon: "tiktok",
    accent: "linear-gradient(135deg,#25f4ee,#000 55%,#fe2c55)",
    size: "icon",
  },
  {
    title: "こまスタンプ",
    url: "https://line.me/S/sticker/33533275/?lang=ja",
    icon: "line",
    accent: "linear-gradient(135deg,#06c755,#04a544)",
    size: "compact",
  },
  {
    title: "こまスタンプPrt2",
    url: "https://line.me/S/sticker/33782414/?lang=ja",
    icon: "line",
    accent: "linear-gradient(135deg,#06c755,#04a544)",
    size: "compact",
  },
  {
    title: "こまスタンプPrt3",
    url: "https://line.me/S/sticker/34081770/?lang=ja",
    icon: "line",
    accent: "linear-gradient(135deg,#06c755,#04a544)",
    size: "compact",
  },
];

/** 背景写真集（photos/ フォルダの中身） */
const PHOTO_COUNT = 22;
const PHOTOS = Array.from(
  { length: PHOTO_COUNT },
  (_, i) => `photos/coma-${String(i + 1).padStart(2, "0")}.jpg`
);

/** 動画の終わり何秒前にリンク欄を出すか（＝こまが近くまで寄ってきた頃） */
const REVEAL_LEAD = 1.5;
/** 動画が再生できなかった場合に、強制的にリンク欄を出すまでの秒数 */
const FAILSAFE_SEC = 9;
/** 写真の切り替え間隔（ミリ秒）— この範囲でランダム */
const SLIDE_MIN_MS = 2000;
const SLIDE_MAX_MS = 3000;
/** 写真を全画面に引き伸ばしてよい下限。
 *  「画面いっぱいにしたときに見える割合」がこの値以上なら全画面（cover）、
 *  下回る写真は切らずに全体を表示し、余白は同じ写真のぼかしで埋める。
 *  0.97 = ほぼ切らない。0.8 くらいにすると縦写真が全画面になり見栄えは上がるが、
 *  端に写っている耳などが少し切れることがある。 */
const COVER_THRESHOLD = 0.97;

/* ========================================================================= */

const ICONS = {
  instagram:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2.8" y="2.8" width="18.4" height="18.4" rx="5.2"/><circle cx="12" cy="12" r="4.3"/><circle cx="17.4" cy="6.6" r="1.2" fill="currentColor" stroke="none"/></svg>',
  tiktok:
    '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.2 2h2.9c.3 2.3 1.8 3.9 4.1 4.1v2.9c-1.6.1-3.1-.4-4.4-1.3v6.6c0 3.9-3.4 6.9-7.4 6.2-2.9-.5-5.1-3-5.3-6-.2-3.6 2.6-6.6 6.2-6.6.3 0 .7 0 1 .1v3.1c-.3-.1-.6-.2-1-.2a3.4 3.4 0 1 0 3.4 3.4V2z"/></svg>',
  line:
    '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6c5.4 0 9.8 3.5 9.8 7.9 0 1.6-.6 3-1.9 4.4-1.9 2.2-6.1 5-7.1 5.4-.9.4-.8-.2-.8-.4l.1-.8c.1-.4.1-.9-.1-1.2-.2-.3-.7-.5-1.1-.6-4.2-.6-7.3-3.5-7.3-6.8 0-4.4 4.4-7.9 8.4-7.9z"/><circle cx="8.6" cy="10.2" r="1.15" fill="#fff"/><circle cx="15.4" cy="10.2" r="1.15" fill="#fff"/><path d="M9.4 13.1c.7.8 1.6 1.2 2.6 1.2s1.9-.4 2.6-1.2" fill="none" stroke="#fff" stroke-width="1.3" stroke-linecap="round"/></svg>',
  link: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 13.5a4 4 0 0 0 5.7.3l3-3A4 4 0 0 0 13 5.2l-1.7 1.7"/><path d="M14 10.5a4 4 0 0 0-5.7-.3l-3 3A4 4 0 0 0 11 18.8l1.7-1.7"/></svg>',
};

/** 動画のアスペクト比（1280x720）。画面比率がこれから離れているとレターボックス表示にする */
const VIDEO_ASPECT = 16 / 9;
const ASPECT_TOLERANCE = 0.2;

const body = document.body;
const intro = document.getElementById("intro");
const video = document.getElementById("intro-video");
const blurVideo = document.getElementById("intro-blur");
const tapToStart = document.getElementById("tap-to-start");
const skipBtn = document.getElementById("skip");
const replayBtn = document.getElementById("replay");
const card = document.getElementById("card");
const linksEl = document.getElementById("links");
const slides = Array.from(document.querySelectorAll(".slide"));

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------- リンク欄を組み立てる ---------- */
function buildLinks() {
  linksEl.innerHTML = "";
  let iconRow = null;

  for (const item of LINKS) {
    const a = document.createElement("a");
    a.className = "link" + (item.size ? ` ${item.size}` : "");
    a.href = item.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.innerHTML =
      `<span class="icon" style="background:${item.accent || ""}">${ICONS[item.icon] || ICONS.link}</span>` +
      `<span class="txt"><span class="title"></span>${item.sub ? '<span class="sub"></span>' : ""}</span>` +
      `<span class="chev" aria-hidden="true">›</span>`;
    a.querySelector(".title").textContent = item.title;
    if (item.sub) a.querySelector(".sub").textContent = item.sub;

    if (item.size === "icon") {
      // アイコンだけのボタンは名前が出ないので、読み上げ用に名前を持たせる
      a.setAttribute("aria-label", item.title);
      a.title = item.title;
      if (!iconRow) {
        iconRow = document.createElement("div");
        iconRow.className = "icon-row";
        linksEl.appendChild(iconRow);
      }
      iconRow.appendChild(a);
    } else {
      iconRow = null;
      linksEl.appendChild(a);
    }
  }
}

/* ---------- 背景の写真集（ランダム・2〜3秒ごとにクロスフェード） ---------- */
let bag = [];
let layer = 0;
let slideTimer = null;
let slideshowRunning = false;

function nextPhoto() {
  if (bag.length === 0) {
    // 全部出しきったら並べ直す（直前の写真が続けて出ないようにする）
    const last = bag.last;
    bag = PHOTOS.slice();
    for (let i = bag.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [bag[i], bag[j]] = [bag[j], bag[i]];
    }
    if (bag[bag.length - 1] === last && bag.length > 1) {
      [bag[bag.length - 1], bag[0]] = [bag[0], bag[bag.length - 1]];
    }
  }
  const pick = bag.pop();
  bag.last = pick;
  return pick;
}

/** 写真の縦横比。読み込めた順に埋まる */
const aspects = new Map();

/** 画面を全面に使っても写真がほとんど切れないなら cover、
 *  大きく切れてしまうなら contain（＝こまの顔が欠けないことを優先） */
function shouldCover(src) {
  const a = aspects.get(src);
  if (!a) return false; // 縦横比が分からないうちは切らない方に倒す
  const screen = window.innerWidth / window.innerHeight;
  const visible = a > screen ? screen / a : a / screen;
  return visible >= COVER_THRESHOLD;
}

/** 画面の向きが変わったときや、後から縦横比が分かったときに表示方法を見直す */
function refreshFit() {
  for (const el of slides) {
    if (el.dataset.src) el.classList.toggle("cover", shouldCover(el.dataset.src));
  }
}

function showPhoto(src) {
  const el = slides[layer % slides.length];
  const prev = slides[(layer + 1) % slides.length];
  const url = `url("${src}")`;
  el.dataset.src = src;
  el.querySelector(".pic").style.backgroundImage = url;
  el.querySelector(".fill").style.backgroundImage = url;
  el.classList.toggle("cover", shouldCover(src));
  el.classList.remove("is-visible");
  void el.offsetWidth; // Ken Burns をやり直すためのリフロー
  el.classList.add("is-visible");
  prev.classList.remove("is-visible");
  layer++;
}

function preload(src) {
  const img = new Image();
  img.decoding = "async";
  img.addEventListener("load", () => {
    if (!img.naturalHeight) return;
    aspects.set(src, img.naturalWidth / img.naturalHeight);
    refreshFit();
  });
  img.src = src;
  return img;
}

/** 次に出す写真を 1 枚先に読み込んでおく（表示前に縦横比を確定させるため） */
let upcoming = null;

function primeNext() {
  upcoming = nextPhoto();
  preload(upcoming);
  return upcoming;
}

function scheduleSlide() {
  const wait = SLIDE_MIN_MS + Math.random() * (SLIDE_MAX_MS - SLIDE_MIN_MS);
  slideTimer = setTimeout(() => {
    showPhoto(upcoming || primeNext());
    primeNext();
    scheduleSlide();
  }, wait);
}

function startSlideshow() {
  if (slideshowRunning) return;
  slideshowRunning = true;
  showPhoto(primeNext());
  primeNext();
  scheduleSlide();
}

function stopSlideshow() {
  clearTimeout(slideTimer);
  slideshowRunning = false;
  slides.forEach((s) => s.classList.remove("is-visible"));
}

/* ---------- 動画の表示方法（見切れる縦画面ではぼかし背景を敷く） ---------- */
let letterbox = false;

function updateVideoFit() {
  const aspect = window.innerWidth / window.innerHeight;
  const ratio = aspect / VIDEO_ASPECT;
  const next = ratio < 1 - ASPECT_TOLERANCE || ratio > 1 + ASPECT_TOLERANCE;
  if (next === letterbox) return;
  letterbox = next;
  intro.classList.toggle("letterbox", letterbox);
  if (letterbox && !blurVideo.src) {
    // 必要になったときだけ読み込む（横長画面では 2 本目をデコードしない）
    blurVideo.src = video.currentSrc || "coma-run.mp4";
    blurVideo.load();
  }
  syncBlur();
}

function syncBlur() {
  if (!letterbox || !blurVideo.src) return;
  try {
    if (Math.abs(blurVideo.currentTime - video.currentTime) > 0.25) {
      blurVideo.currentTime = video.currentTime;
    }
  } catch (_) {
    /* metadata 未読み込み時は無視 */
  }
  if (video.paused) blurVideo.pause();
  else blurVideo.play().catch(() => {});
}

/* ---------- 動画 → リンク欄への切り替え ---------- */
let revealed = false;
let failsafeTimer = null;

function reveal() {
  if (revealed) return;
  revealed = true;
  clearTimeout(failsafeTimer);
  tapToStart.hidden = true;
  skipBtn.style.display = "none";
  card.hidden = false;
  startSlideshow();
  body.classList.add("is-revealed");
  // フェードアウトが終わってから動画を DOM から消す
  setTimeout(() => {
    body.classList.add("intro-done");
    video.pause();
    blurVideo.pause();
  }, 1600);
}

function onTimeUpdate() {
  syncBlur();
  const d = video.duration;
  if (!isFinite(d) || d <= 0) return;
  if (video.currentTime >= Math.max(d - REVEAL_LEAD, d * 0.55)) reveal();
}

function playIntro() {
  const p = video.play();
  if (p && typeof p.catch === "function") {
    p.catch(() => {
      // 自動再生がブロックされた場合はタップを促す
      tapToStart.hidden = false;
    });
  }
  syncBlur();
}

function startIntro() {
  revealed = false;
  body.classList.remove("is-revealed", "intro-done");
  card.hidden = true;
  skipBtn.style.display = "";
  stopSlideshow();
  try {
    video.currentTime = 0;
    blurVideo.currentTime = 0;
  } catch (_) {
    /* まだ metadata が無い場合は無視 */
  }
  playIntro();
  clearTimeout(failsafeTimer);
  failsafeTimer = setTimeout(reveal, FAILSAFE_SEC * 1000);
}

/* ---------- 起動 ---------- */
buildLinks();
updateVideoFit();
PHOTOS.slice(0, 3).forEach(preload); // 最初の数枚だけ先読みしておく

window.addEventListener("resize", () => {
  updateVideoFit();
  refreshFit();
});
window.addEventListener("orientationchange", () => {
  updateVideoFit();
  refreshFit();
});
video.addEventListener("play", syncBlur);
video.addEventListener("timeupdate", onTimeUpdate);
video.addEventListener("ended", reveal);
video.addEventListener("error", reveal);

skipBtn.addEventListener("click", reveal);
tapToStart.addEventListener("click", () => {
  tapToStart.hidden = true;
  playIntro();
});
replayBtn.addEventListener("click", startIntro);

if (reducedMotion) {
  // アニメーションを控える設定の端末では、動画を飛ばしてリンク欄を出す
  intro.style.display = "none";
  reveal();
} else {
  startIntro();
}
