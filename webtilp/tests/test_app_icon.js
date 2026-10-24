'use strict';

// app-icon.js points the icon and manifest links at the default theme's icon set.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'app-icon.js'), 'utf8');
const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'webtilp.html'), 'utf8');
const files = ['favicon-32x32.png', 'favicon-16x16.png', 'favicon.ico', 'apple-touch-icon.png', 'site.webmanifest'];

function run(storedTheme, { blockStorage = false } = {}) {
    const links = files.map(file => {
        const attributes = new Map([['href', file]]);
        return {
            dataset: {},
            getAttribute: name => attributes.get(name),
            setAttribute: (name, value) => attributes.set(name, value)
        };
    });
    const context = vm.createContext({
        document: { querySelectorAll: () => links },
        localStorage: {
            getItem: key => {
                if (blockStorage) throw new Error('blocked');
                return key === 'webtilp.theme' ? storedTheme : null;
            }
        }
    });
    vm.runInContext(source, context);
    const hrefs = () => links.map(link => link.getAttribute('href'));
    return { hrefs, apply: theme => context.TIConnectMCAppIcon.apply(theme) };
}

// Every theme in app.js has an icon set, and every set has all the files.
const themeIds = [...app.matchAll(/\{ id: '([a-z-]+)', labelKey:/g)].map(match => match[1]);
assert.ok(themeIds.length >= 11, 'found the THEMES list');
const sets = new Set();
for (const theme of themeIds) {
    const icon = run(theme);
    const folders = new Set(icon.hrefs().map(href => href.slice(0, href.lastIndexOf('/') + 1)));
    assert.equal(folders.size, 1, `${theme}: all links use one icon set`);
    const [folder] = folders;
    if (theme.startsWith('minecraft')) {
        assert.equal(folder, '', 'Minecraft themes keep the root icons');
    } else {
        assert.match(folder, /^themes\/icons\/[a-z]+\/$/, `${theme} has its own icon set`);
    }
    sets.add(folder);
    for (const href of icon.hrefs()) {
        assert.ok(fs.existsSync(path.join(root, href)), `${href} exists`);
    }
}
assert.ok(sets.size >= 7, 'the themes have distinct icon sets');

// Each set's manifest is the same app as the root one (same start URL, no id).
const rootManifest = JSON.parse(fs.readFileSync(path.join(root, 'site.webmanifest'), 'utf8'));
for (const folder of sets) {
    const manifest = JSON.parse(fs.readFileSync(path.join(root, folder, 'site.webmanifest'), 'utf8'));
    const base = new URL(folder + 'site.webmanifest', 'https://example.test/app/');
    assert.equal(new URL(manifest.start_url, base).href, 'https://example.test/app/' + rootManifest.start_url, `${folder || 'root'} manifest keeps the start URL`);
    assert.equal(manifest.id, undefined);
    assert.equal(manifest.name, rootManifest.name);
    for (const icon of manifest.icons) {
        assert.ok(fs.existsSync(path.join(root, folder, icon.src)), `${folder}${icon.src} exists`);
    }
}

// Unknown, missing or unreadable defaults keep the Minecraft icons; switching
// back and forth rewrites the links.
assert.deepEqual(run('no-such-theme').hrefs(), files);
assert.deepEqual(run(null).hrefs(), files);
assert.deepEqual(run('cyberpunk', { blockStorage: true }).hrefs(), files);
const icon = run('modern');
assert.deepEqual(icon.hrefs(), files.map(file => `themes/icons/modern/${file}`));
icon.apply('retro');
assert.deepEqual(icon.hrefs(), files.map(file => `themes/icons/retro/${file}`));
icon.apply('minecraft-night');
assert.deepEqual(icon.hrefs(), files);

// The script runs in <head>, after the links it rewrites.
const head = html.slice(0, html.indexOf('</head>'));
assert.ok(head.indexOf('<script src="app-icon.js"></script>') > head.indexOf('rel="manifest"'));

console.log('App icon tests passed (every theme has a complete icon set, manifests keep the app identity, link switching)');
