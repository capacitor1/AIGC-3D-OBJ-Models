const puppeteer = require('puppeteer-core');
(async()=>{
  const args=process.argv.slice(2);
  const view=args[0]||'frontleft';
  const file=args[1]||'open';
  const out=args[2]||`render/${view}.png`;
  const w=parseInt(args[3]||'1400',10), h=parseInt(args[4]||'1000',10);
  const browser=await puppeteer.launch({
    executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless:'new',
    args:['--no-sandbox','--disable-gpu','--enable-unsafe-swiftshader','--allow-file-access-from-files','--hide-scrollbars']
  });
  const page=await browser.newPage();
  await page.setViewport({width:w,height:h,deviceScaleFactor:1});
  page.on('console',msg=>console.log('PAGE:',msg.text()));
  page.on('pageerror',err=>console.log('PAGEERR:',err.message));
  await page.goto(`http://127.0.0.1:8123/render/viewer.html?view=${view}&file=${file}&w=${w}&h=${h}`,{waitUntil:'load',timeout:60000});
  await page.waitForFunction('window.__ready===true',{timeout:120000});
  await new Promise(r=>setTimeout(r,1200));
  await page.screenshot({path:out});
  console.log('saved',out);
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
