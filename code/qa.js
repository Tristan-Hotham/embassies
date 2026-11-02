// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server PORT; set PORT). Leaflet and Supercluster come
// from a local npm copy (NPM_DIR/node_modules) because the CDNs are not reachable from the build container; tiles are blocked.
const { chromium } = require("playwright");
const fs = require("fs");
const NM = process.env.NPM_DIR + "/node_modules";
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch();
  const errs = [];
  for (const [nm, vw, vh] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet\.min\.js/, r => r.fulfill({ path: NM + "/leaflet/dist/leaflet.js", contentType: "application/javascript" }));
    await p.route(/leaflet\.min\.css/, r => r.fulfill({ path: NM + "/leaflet/dist/leaflet.css", contentType: "text/css" }));
    await p.route(/supercluster\.min\.js/, r => r.fulfill({ path: NM + "/supercluster/dist/supercluster.min.js", contentType: "application/javascript" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + process.env.PORT + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(3000);
    const jpg = f => `qa/${nm}_${f}.jpg`;
    await p.screenshot({ path: jpg("top"), type: "jpeg", quality: 70 });
    const shot = async (sel, f) => { await p.locator(sel).first().scrollIntoViewIfNeeded(); await p.waitForTimeout(600); await p.locator(sel).first().screenshot({ path: jpg(f), type: "jpeg", quality: 72 }); };
    await shot(".mapgrid", "map_world");
    await p.locator("#colRow .btn[data-k=abroad]").click(); await p.waitForTimeout(500); await shot(".mapgrid", "map_abroad");
    await p.fill("#q", "Holy See"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(1800); await shot(".mapgrid", "sel_holysee");
    await p.fill("#q", "Taiwan"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(1800); await shot(".mapgrid", "sel_taiwan");
    await p.fill("#q", "Nigeria"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(1500);
    await p.locator("#viewRow .btn[data-v=home]").click(); await p.waitForTimeout(2200); await shot(".mapgrid", "sel_nigeria_home");
    await p.locator("#viewRow .btn[data-v=clear]").click(); await p.waitForTimeout(1200);
    await p.fill("#q", "Geneva"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(2200); await shot(".mapgrid", "city_geneva");
    const box = await p.locator("#map").boundingBox();
    await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(800); await shot("#map", "click_point");
    await p.locator(".lyrBtn").click(); await p.waitForTimeout(300); await shot("#map", "layers");
    await p.locator(".lyrPanel select[data-k=base]").selectOption("relief"); await p.waitForTimeout(500);
    await p.locator(".lyrPanel .reset").click({ force: true }); await p.locator(".lyrBtn").click();
    await p.fill("#q", "Washington"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(2000);
    await p.evaluate(() => { let done = 0; ptsL.eachLayer(l => { if (!done++) l.fire("click"); }); }); await p.waitForTimeout(700); await shot("#map", "popup");
    for (const c of ["#netChart", "#lowyTable", "#cityChart", "#consChart", "#clusterTable", "#seatTable", "#smallTable", "#nbTable", "#webChart", "#ambChart", ".three", "#covTable"]) await shot(c, "c_" + c.replace(/[#.]/g, ""));
    await shot("#tlbox", "tl_start");
    for (const [y, f] of [["166", "tl_166"], ["1446", "tl_1446"], ["1817", "tl_1817"], ["1960", "tl_1960"], ["Today", "tl_today"]]) { await p.locator("#tlJump .btn", { hasText: y }).click(); await p.waitForTimeout(900); await shot("#tlbox", f); }
    await p.locator("#tlJump .btn", { hasText: "166" }).click(); await p.waitForTimeout(700);
    await p.evaluate(() => tmap.fire("click", {latlng: L.latLng(41.9, 12.48)})); await p.waitForTimeout(500); await shot("#tlbox", "tl_popup");
    await p.locator("#tlplay").click(); await p.waitForTimeout(2200); await p.locator("#tlplay").click();
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(800); await shot(".mapgrid", "dark_map"); await shot("#webChart", "dark_chart");
      await p.locator(".mapgrid .mfs-btn").click(); await p.waitForTimeout(1200); await p.screenshot({ path: jpg("fullscreen"), type: "jpeg", quality: 70 });
      await p.locator(".mapgrid .mfs-btn").click(); await p.waitForTimeout(600);
      await p.locator("#tlbox .mfs-btn").click(); await p.waitForTimeout(1200); await p.screenshot({ path: jpg("fullscreen_tl"), type: "jpeg", quality: 70 });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov, "fullscreen buttons:", await p.locator(".mfs-btn").count());
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
