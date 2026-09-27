// 카드뉴스(1080x1350)와 유튜브 썸네일(1280x720) PNG 생성기
// 사용법: npm install && npm run build
// 한글 폰트: 'Noto Sans KR'가 시스템에 설치되어 있어야 합니다 (Google Fonts에서 무료 배포).
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { cardSets, thumbnails, HANDLE, DEPT } from './slides.mjs';

// 브랜드 색상: 대학 공식 UI 색상이 있으면 여기만 바꾸면 됩니다.
const C = {
  navy: '#0B2A5B',
  navyDeep: '#071C3F',
  yellow: '#FFC83D',
  mint: '#35C3B0',
  paper: '#F6F4EE',
  ink: '#14213D',
  muted: '#5B6478',
};

const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
// 가운뎃점 앞에서 줄이 바뀌지 않도록 고정 공백 사용
const dots = (s) => String(s).replace(/ · /g, '\u00a0· ');
const br = (s) => esc(s).replace(/\n/g, '<br>');

const baseCss = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Noto Sans KR', sans-serif; word-break: keep-all; }
  .frame { width: 1080px; height: 1350px; position: relative; overflow: hidden; padding: 96px 88px; }
  .top { position: absolute; top: 56px; left: 88px; right: 88px; display: flex; justify-content: space-between;
         font-size: 26px; font-weight: 700; letter-spacing: -0.01em; }
  .foot { position: absolute; bottom: 52px; left: 88px; right: 88px; display: flex; justify-content: space-between;
          font-size: 24px; font-weight: 500; }
  .page { font-variant-numeric: tabular-nums; }
  .dark { background: ${C.navy}; color: #fff; }
  .dark .top, .dark .foot { color: rgba(255,255,255,.72); }
  .light { background: ${C.paper}; color: ${C.ink}; }
  .light .top, .light .foot { color: ${C.muted}; }
  .grid { position: absolute; inset: 0; background-image:
          linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px);
          background-size: 54px 54px; }
  h2 { font-size: 72px; font-weight: 900; line-height: 1.22; letter-spacing: -0.03em; margin-top: 90px; }
  h2 .bar { display: block; width: 88px; height: 10px; background: ${C.yellow}; margin-bottom: 36px; }
`;

function cover(s) {
  return `
  <div class="frame dark">
    <div class="grid"></div>
    <div style="position:absolute; right:-160px; top:220px; width:620px; height:620px; border-radius:50%;
                border: 70px solid ${C.mint}; opacity:.22"></div>
    <div style="position:absolute; left:88px; right:88px; top:360px;">
      <div style="display:inline-block; background:${C.yellow}; color:${C.navyDeep}; font-size:36px; font-weight:900;
                  padding:12px 26px; border-radius:6px;">${esc(s.kicker)}</div>
      <h1 style="font-size:124px; font-weight:900; line-height:1.14; letter-spacing:-0.04em; margin-top:44px;">${br(s.title)}</h1>
      <p style="font-size:40px; font-weight:500; margin-top:44px; color:rgba(255,255,255,.85)">${esc(s.sub)}</p>
    </div>
    <div style="position:absolute; left:88px; bottom:150px; font-size:30px; font-weight:700; color:${C.yellow}">
      옆으로 넘겨 보세요 &rarr;</div>
  </div>`;
}

function list(s) {
  const items = s.items
    .map(
      (it, i) => `
      <div style="display:flex; gap:34px; padding:40px 0; border-top:2px solid rgba(20,33,61,.12)">
        <div style="flex:none; width:76px; height:76px; border-radius:50%; background:${C.navy}; color:${C.yellow};
                    display:flex; align-items:center; justify-content:center; font-size:36px; font-weight:900">${i + 1}</div>
        <div>
          <div style="font-size:48px; font-weight:900; letter-spacing:-0.02em">${esc(it.head)}</div>
          <div style="font-size:36px; font-weight:500; color:${C.muted}; margin-top:12px; line-height:1.45">${esc(it.body)}</div>
        </div>
      </div>`,
    )
    .join('');
  return `
  <div class="frame light">
    <h2><span class="bar"></span>${br(s.title)}</h2>
    <div style="margin-top:64px">${items}</div>
  </div>`;
}

function check(s) {
  const items = s.items
    .map(
      (t) => `
      <div style="display:flex; align-items:center; gap:30px; background:#fff; border-radius:18px; padding:24px 36px;
                  margin-bottom:18px; box-shadow:0 2px 0 rgba(20,33,61,.08)">
        <div style="flex:none; width:52px; height:52px; border:5px solid ${C.navy}; border-radius:10px"></div>
        <div style="font-size:36px; font-weight:700; line-height:1.4; letter-spacing:-0.02em">${esc(t)}</div>
      </div>`,
    )
    .join('');
  return `
  <div class="frame light">
    <h2 style="font-size:64px"><span class="bar"></span>${br(s.title)}</h2>
    <div style="margin-top:52px">${items}</div>
    <div style="margin-top:30px; font-size:30px; font-weight:700; color:${C.navy}">${esc(s.note)}</div>
  </div>`;
}

function versus(s) {
  return `
  <div class="frame light">
    <div style="font-size:200px; font-weight:900; color:${C.navy}; opacity:.1; position:absolute; right:80px; top:120px; line-height:1">
      ${String(s.no).padStart(2, '0')}</div>
    <div style="margin-top:230px; background:#fff; border-radius:28px; padding:56px 60px; border:4px dashed #C9CCD6">
      <div style="font-size:34px; font-weight:900; color:#B5485A">오해</div>
      <div style="font-size:60px; font-weight:900; line-height:1.3; letter-spacing:-0.03em; margin-top:18px;
                  text-decoration: line-through; text-decoration-thickness:5px; text-decoration-color: rgba(181,72,90,.6)">
        ${esc(s.myth)}</div>
    </div>
    <div style="text-align:center; font-size:60px; color:${C.navy}; margin:30px 0">&darr;</div>
    <div style="background:${C.navy}; color:#fff; border-radius:28px; padding:56px 60px">
      <div style="font-size:34px; font-weight:900; color:${C.yellow}">진실</div>
      <div style="font-size:50px; font-weight:700; line-height:1.45; letter-spacing:-0.02em; margin-top:18px">${esc(s.fact)}</div>
    </div>
  </div>`;
}

function exam(s) {
  const rows = s.rows
    .map(
      (r) => `
      <div style="display:flex; gap:34px; padding:38px 0; border-top:2px solid rgba(20,33,61,.12)">
        <div style="flex:none; width:250px; font-size:34px; font-weight:900; color:${C.navy}">${esc(r.label)}</div>
        <div style="font-size:38px; font-weight:500; line-height:1.45">${esc(dots(r.value))}</div>
      </div>`,
    )
    .join('');
  return `
  <div class="frame light">
    <h2><span class="bar"></span>${br(s.title)}</h2>
    <div style="font-size:32px; font-weight:700; color:${C.muted}; margin-top:18px">${esc(s.org)}</div>
    <div style="margin-top:48px">${rows}</div>
    <div style="margin-top:24px; font-size:28px; color:${C.muted}">※ ${esc(s.note)}</div>
  </div>`;
}

function cta(s) {
  const buttons = s.buttons
    .map(
      (b, i) => `
      <div style="border-radius:999px; padding:30px 44px; font-size:38px; font-weight:900; margin-top:26px;
                  ${i === 0 ? `background:${C.yellow}; color:${C.navyDeep}` : 'border:4px solid rgba(255,255,255,.6)'}">
        ${esc(b)}</div>`,
    )
    .join('');
  return `
  <div class="frame dark">
    <div class="grid"></div>
    <div style="position:absolute; left:88px; right:88px; top:300px">
      <h1 style="font-size:96px; font-weight:900; line-height:1.2; letter-spacing:-0.04em">${br(s.title)}</h1>
      <p style="font-size:38px; font-weight:500; margin-top:36px; line-height:1.5; color:rgba(255,255,255,.85)">${esc(s.sub)}</p>
      <div style="margin-top:70px">${buttons}</div>
    </div>
  </div>`;
}

const render = { cover, list, check, versus, exam, cta };

function slideHtml(s, i, total) {
  const body = render[s.type](s);
  // 머리글·바닥글은 공통으로 덧붙임
  const chrome = `
    <div class="top"><span>${esc(DEPT)}</span><span class="page">${i + 1} / ${total}</span></div>
    <div class="foot"><span>${esc(HANDLE)}</span><span>저장 · 공유</span></div>`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>${baseCss}</style></head>
    <body>${body.replace(/<\/div>\s*$/, chrome + '</div>')}</body></html>`;
}

function thumbHtml(t) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>${baseCss}</style></head><body>
  <div style="width:1280px; height:720px; position:relative; overflow:hidden; background:${C.navy}; color:#fff; padding:70px 80px">
    <div class="grid"></div>
    <div style="position:absolute; right:-120px; bottom:-160px; width:560px; height:560px; border-radius:50%;
                border:64px solid ${C.mint}; opacity:.25"></div>
    <div style="position:relative">
      <div style="display:inline-block; background:${C.mint}; color:${C.navyDeep}; font-size:34px; font-weight:900;
                  padding:8px 22px; border-radius:6px">${esc(t.tag)}</div>
      <div style="font-size:44px; font-weight:700; margin-top:40px; color:${C.yellow}">${esc(t.kicker)}</div>
      <div style="font-size:112px; font-weight:900; line-height:1.14; letter-spacing:-0.04em; margin-top:16px;
                  text-shadow:0 6px 0 ${C.navyDeep}">${br(t.title)}</div>
    </div>
    <div style="position:absolute; left:80px; bottom:56px; font-size:30px; font-weight:700; color:rgba(255,255,255,.75)">
      ${esc(DEPT)}</div>
  </div></body></html>`;
}

const browser = await chromium.launch(
  process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
);
const page = await browser.newPage({ deviceScaleFactor: 1 });

for (const set of cardSets) {
  const dir = new URL(`./output/${set.id}/`, import.meta.url);
  await mkdir(dir, { recursive: true });
  for (const [i, s] of set.slides.entries()) {
    await page.setViewportSize({ width: 1080, height: 1350 });
    await page.setContent(slideHtml(s, i, set.slides.length), { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const file = new URL(`${String(i + 1).padStart(2, '0')}.png`, dir);
    await page.screenshot({ path: fileURLToPath(file), clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  }
  console.log(`카드뉴스 ${set.id}: ${set.slides.length}장`);
}

const tdir = new URL('./output/youtube_thumbnails/', import.meta.url);
await mkdir(tdir, { recursive: true });
for (const t of thumbnails) {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.setContent(thumbHtml(t), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: fileURLToPath(new URL(`${t.id}.png`, tdir)), clip: { x: 0, y: 0, width: 1280, height: 720 } });
  console.log(`썸네일 ${t.id}`);
}

await browser.close();
