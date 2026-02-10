const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });

  // Unauthenticated pages first
  const publicContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const publicPage = await publicContext.newPage();

  // Login page
  try {
    await Promise.race([
      publicPage.goto('http://localhost:4201/auth/login', { waitUntil: 'networkidle' }),
      new Promise(r => setTimeout(r, 8000))
    ]);
    await new Promise(r => setTimeout(r, 2000));
    await publicPage.screenshot({ path: '../audit-login.png', fullPage: true });
    console.log('1. Login captured');
  } catch(e) { console.error('Login error:', e.message); }

  // Forgot password
  try {
    await Promise.race([
      publicPage.goto('http://localhost:4201/auth/forgot-password', { waitUntil: 'networkidle' }),
      new Promise(r => setTimeout(r, 8000))
    ]);
    await new Promise(r => setTimeout(r, 2000));
    await publicPage.screenshot({ path: '../audit-forgot-password.png', fullPage: true });
    console.log('2. Forgot password captured');
  } catch(e) { console.error('Forgot password error:', e.message); }

  // Portal login
  try {
    await Promise.race([
      publicPage.goto('http://localhost:4201/portal/login', { waitUntil: 'networkidle' }),
      new Promise(r => setTimeout(r, 8000))
    ]);
    await new Promise(r => setTimeout(r, 2000));
    await publicPage.screenshot({ path: '../audit-portal-login.png', fullPage: true });
    console.log('3. Portal login captured');
  } catch(e) { console.error('Portal login error:', e.message); }

  await publicContext.close();

  // Authenticated pages
  const authContext = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    storageState: {
      cookies: [],
      origins: [{
        origin: 'http://localhost:4201',
        localStorage: [
          { name: 'bayan_access_token', value: 'fake-token' },
          { name: 'bayan_remember_me', value: 'true' },
          { name: 'bayan_user', value: JSON.stringify({ id: '1', firstName: 'Omar', lastName: 'Admin', email: 'admin@bayan.com', role: 'admin' }) }
        ]
      }]
    }
  });

  const pages = [
    { url: '/dashboard', name: 'dashboard' },
    { url: '/tenders', name: 'tender-list' },
    { url: '/tenders/new', name: 'tender-wizard' },
    { url: '/admin/users', name: 'admin-users' },
    { url: '/admin/clients', name: 'admin-clients' },
    { url: '/admin/bidders', name: 'admin-bidders' },
    { url: '/admin/settings', name: 'admin-settings' },
  ];

  let i = 4;
  for (const p of pages) {
    const page = await authContext.newPage();
    try {
      await Promise.race([
        page.goto('http://localhost:4201' + p.url, { waitUntil: 'networkidle' }),
        new Promise(r => setTimeout(r, 10000))
      ]);
      await new Promise(r => setTimeout(r, 3000));
      await page.screenshot({ path: `../audit-${p.name}.png`, fullPage: false });
      console.log(`${i}. ${p.name} captured`);
    } catch(e) {
      console.error(`${p.name} error:`, e.message);
      try {
        await page.screenshot({ path: `../audit-${p.name}.png`, fullPage: false });
        console.log(`${i}. ${p.name} captured (after error)`);
      } catch(e2) {}
    }
    await Promise.race([page.close(), new Promise(r => setTimeout(r, 3000))]);
    i++;
  }

  await Promise.race([browser.close(), new Promise(r => setTimeout(r, 5000))]);
  process.exit(0);
})();
