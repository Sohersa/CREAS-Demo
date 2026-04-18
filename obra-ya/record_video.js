// Record showcase.html to a webm video using Playwright.
// Usage: node record_video.js
// Output: obraya_showcase.webm (40s, 1920x1080)

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  console.log('🎬 Starting ObraYa showcase recording...');

  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-web-security', '--no-sandbox'],
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: './',
      size: { width: 1920, height: 1080 },
    },
  });

  const page = await context.newPage();

  const showcaseFile = path.resolve(__dirname, 'showcase.html');
  const url = 'file:///' + showcaseFile.replace(/\\/g, '/');
  console.log('📄 Loading:', url);

  await page.goto(url);
  await page.waitForLoadState('networkidle');

  console.log('⏱️  Recording for 40 seconds...');
  // Wait for one full loop (40s)
  await page.waitForTimeout(40500);

  console.log('💾 Saving video...');
  await page.close();
  await context.close();
  await browser.close();

  // Find the recorded video
  const files = fs.readdirSync('./').filter(f => f.endsWith('.webm'));
  if (files.length > 0) {
    const latest = files.sort((a, b) => {
      return fs.statSync(b).mtime - fs.statSync(a).mtime;
    })[0];
    fs.renameSync(latest, 'obraya_showcase.webm');
    console.log('✅ Video saved: obraya_showcase.webm');
    const size = (fs.statSync('obraya_showcase.webm').size / 1024 / 1024).toFixed(2);
    console.log(`   Size: ${size} MB`);
  }
})().catch(err => {
  console.error('❌ Error:', err);
  process.exit(1);
});
