'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = fs.readFileSync(require.resolve('../app.js'), 'utf8');

function extractFunction(name) {
    const start = app.indexOf(`function ${name}(`);
    assert.notEqual(start, -1, `${name} exists`);
    const bodyStart = app.indexOf(') {', start) + 2;
    let depth = 0;
    for (let i = bodyStart; i < app.length; i++) {
        if (app[i] === '{') depth++;
        if (app[i] === '}') depth--;
        if (!depth) return app.slice(start, i + 1);
    }
    throw new Error(`Unterminated function ${name}`);
}

function decode(text) {
    return text.replace(/&(?:amp|lt|gt|quot|#39);/g, entity => ({
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'"
    })[entity]);
}

// This mock models the DOM operations used by theme changes. In particular,
// replacing innerHTML removes the old children, so identity assertions detect
// an accidental rebuild of a button, selection row, or sticky folder header.
class Element {
    constructor(classes = '') {
        this.classes = new Set(classes.split(/\s+/).filter(Boolean));
        this.children = [];
        this.dataset = {};
        this.disabled = false;
        this.hidden = false;
        this.attributes = new Map();
        this.classList = {
            add: name => this.classes.add(name),
            remove: name => this.classes.delete(name),
            contains: name => this.classes.has(name)
        };
    }
    set innerHTML(value) {
        this.html = value;
        this.children = [];
        // Parse the generated glyph spans; SVG details stay as their contents.
        for (const match of value.matchAll(/<span class="theme-icon" data-icon="([^"]*)" data-emoji="([^"]*)" aria-hidden="true">([\s\S]*?)<\/span>/g)) {
            const glyph = new Element('theme-icon');
            glyph.dataset = { icon: decode(match[1]), emoji: decode(match[2]) };
            glyph.innerHTML = match[3];
            this.children.push(glyph);
        }
        // Theme picker options and their "Default" badge.
        for (const match of value.matchAll(/<button type="button" class="theme-option" data-theme-id="([^"]*)" aria-pressed="(true|false)">[\s\S]*?<span class="theme-option-badge"( hidden)?>[^<]*<\/span><\/button>/g)) {
            const option = new Element('theme-option');
            option.dataset = { themeId: decode(match[1]) };
            option.setAttribute('aria-pressed', match[2]);
            const badge = option.appendChild(new Element('theme-option-badge'));
            badge.hidden = Boolean(match[3]);
            this.children.push(option);
        }
    }
    setAttribute(name, value) { this.attributes.set(name, String(value)); }
    getAttribute(name) { return this.attributes.get(name) ?? null; }
    get innerHTML() { return this.html || ''; }
    set textContent(value) {
        this.text = value;
        this.html = '';
        this.children = [];
    }
    get textContent() { return this.text ?? decode(this.innerHTML.replace(/<[^>]*>/g, '')); }
    appendChild(child) { this.children.push(child); return child; }
    querySelectorAll(selector) {
        assert.ok(selector.startsWith('.'), 'only class selectors are needed');
        return this.children.flatMap(child => [
            ...(child.classes.has(selector.slice(1)) ? [child] : []),
            ...child.querySelectorAll(selector)
        ]);
    }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
}

const body = new Element();
const storage = new Map();
const session = new Map();
const themeList = new Element();
const setDefaultButton = new Element('btn');
const context = vm.createContext({
    document: { body, querySelectorAll: selector => body.querySelectorAll(selector) },
    localStorage: {
        getItem: key => storage.get(key) ?? null,
        setItem: (key, value) => storage.set(key, value)
    },
    sessionStorage: {
        getItem: key => session.get(key) ?? null,
        setItem: (key, value) => session.set(key, value)
    },
    els: { themeList, btnSetDefaultTheme: setDefaultButton },
    t: key => key,
    getOptionLabel: option => option.labelKey,
    applyTranslations() { assert.fail('changing theme must not reset device capabilities or loading controls'); },
    renderDirlist() { assert.fail('changing theme must not rebuild selected rows'); }
});
vm.runInContext(app.slice(app.indexOf('const SITE_DEFAULT_THEME ='),
    app.indexOf('function getCalcModelLabel(')), context);
for (const name of ['escapeHtml', 'themeUsesIcons', 'iconMarkup', 'themeIconMarkup',
    'setIconLabel', 'updateThemeIcons', 'applyTheme', 'setDefaultTheme',
    'themePreviewMarkup', 'renderThemePicker', 'updateThemePicker', 'initTheme',
    'setButtonLoading']) {
    vm.runInContext(extractFunction(name), context);
}

const siteDefault = vm.runInContext('SITE_DEFAULT_THEME', context);
const themeDefs = vm.runInContext('THEMES', context);
const themes = Array.from(themeDefs, theme => theme.id);
const iconThemes = new Set(themeDefs.filter(theme => theme.icons === 'svg').map(theme => theme.id));
assert.ok(themes.includes(siteDefault), 'the site default is a listed theme');
assert.ok(themes.includes('cyberpunk') && themes.includes('modern'), 'new themes are listed');
assert.deepEqual([...iconThemes].sort(), ['minimal', 'modern'], 'Minimal and Modern draw icons');
for (const theme of themeDefs) {
    assert.ok(theme.preview.length >= 1 && theme.preview.every(colors => colors.length === 4), `${theme.id} has a preview`);
}

// A first visit opens with the site default and lists every theme.
context.initTheme();
assert.equal(body.dataset.theme, siteDefault);
const options = themeList.querySelectorAll('.theme-option');
assert.deepEqual(options.map(option => option.dataset.themeId), themes, 'the picker lists every theme in order');
const optionBadges = options.map(option => option.querySelector('.theme-option-badge'));
const settings = body.appendChild(new Element('btn'));
const badge = settings.appendChild(new Element('settings-update-dot hidden'));
context.setIconLabel(settings, 'settings', 'Settings & options', '⚙️');
assert.equal(settings.querySelector('.settings-update-dot'), badge);
context.setIconLabel(null, 'settings', 'optional control', '⚙️');

const send = body.appendChild(new Element('btn'));
context.setIconLabel(send, 'upload', 'Send files', '📤');
context.setButtonLoading(send, true);
const hiddenAction = body.appendChild(new Element('btn hidden'));
context.setIconLabel(hiddenAction, 'download', 'Unavailable operation', '⬇️');

const row = body.appendChild(new Element('is-active'));
row.innerHTML = context.themeIconMarkup('eye', '👁️') + context.themeIconMarkup('folder', '📂');
const selection = row.appendChild(new Element());
selection.checked = true;
selection.dataset.name = 'PROGRAM';
const sticky = body.appendChild(new Element('folder-sticky-name'));
sticky.innerHTML = context.themeIconMarkup('folder', '📂') + ' main';
const glyphs = body.querySelectorAll('.theme-icon');
const children = new Map([settings, send, hiddenAction, row, sticky]
    .map(element => [element, [...element.children]]));

// Pick every theme twice, as from the picker, and set one as the default on
// the way. This includes changing an already rendered row and sticky header
// in both directions.
let expectedDefault = siteDefault;
for (let i = 0; i < themes.length * 2; i++) {
    const theme = themes[(i + 1) % themes.length];
    context.applyTheme(theme);
    if (i === 3) {
        context.setDefaultTheme(theme);
        expectedDefault = theme;
    }
    assert.equal(body.dataset.theme, theme);
    assert.equal(session.get('ticonnectmc.sessionTheme'), theme, 'a picked theme lasts for this tab');
    assert.equal(storage.get('webtilp.theme'), i >= 3 ? expectedDefault : undefined, 'only Set as default changes the default');
    const current = themeList.querySelectorAll('.theme-option');
    current.forEach((option, index) => {
        assert.equal(option, options[index], 'picker options are not recreated');
        assert.equal(option.querySelector('.theme-option-badge'), optionBadges[index]);
        assert.equal(option.getAttribute('aria-pressed'), String(option.dataset.themeId === theme));
        assert.equal(optionBadges[index].hidden, option.dataset.themeId !== expectedDefault);
    });
    assert.equal(setDefaultButton.disabled, theme === expectedDefault);
    assert.ok(setDefaultButton.textContent.includes(theme === expectedDefault ? 'theme_is_default' : 'theme_set_default'));
    for (const glyph of glyphs) {
        if (iconThemes.has(theme)) {
            assert.match(glyph.innerHTML, /<svg class="icon" aria-hidden="true">/);
            assert.ok(glyph.innerHTML.includes(`href="#icon-${glyph.dataset.icon}"`));
        } else {
            assert.equal(glyph.textContent, glyph.dataset.emoji);
        }
    }
    for (const [element, original] of children) {
        assert.equal(element.children.length, original.length);
        element.children.forEach((child, index) => assert.equal(child, original[index], 'controls are not recreated'));
    }
    assert.equal(settings.querySelector('.settings-update-dot'), badge, 'update badge identity survives');
    assert.equal(send.disabled, true, 'an in-flight transfer stays disabled');
    assert.equal(send.classList.contains('loading'), true);
    assert.equal(send.dataset.prevDisabled, '0');
    assert.equal(hiddenAction.classList.contains('hidden'), true);
    assert.equal(selection.checked, true, 'selected variables survive');
    assert.equal(selection.dataset.name, 'PROGRAM');
    assert.equal(row.classList.contains('is-active'), true);
}
context.setButtonLoading(send, false);
assert.equal(send.disabled, false, 'loading cleanup still restores the original state');
context.applyTheme('unknown-theme');
assert.equal(body.dataset.theme, expectedDefault, 'unknown themes use the default');
context.setDefaultTheme('unknown-theme');
assert.equal(storage.get('webtilp.theme'), expectedDefault, 'an unknown theme is never saved as the default');

// Start-up order: the theme being tried in this tab, then the device default,
// then the site default (also when the saved default no longer exists).
session.set('ticonnectmc.sessionTheme', 'retro');
context.initTheme();
assert.equal(body.dataset.theme, 'retro');
session.clear();
context.initTheme();
assert.equal(body.dataset.theme, expectedDefault);
storage.set('webtilp.theme', 'removed-theme');
session.clear();
context.initTheme();
assert.equal(body.dataset.theme, siteDefault);
assert.equal(themeList.querySelectorAll('.theme-option').length, themes.length);

// Translated labels and emoji metadata are text, including when they contain
// markup delimiters. Switching back to emoji uses textContent, not HTML.
const escaped = body.appendChild(new Element('btn'));
const label = '<img src=x> "quoted" & \'apostrophe\'';
const emoji = '<glyph> " & \' ';
context.setIconLabel(escaped, 'info', label, emoji);
assert.ok(escaped.innerHTML.includes('&lt;img src=x&gt; &quot;quoted&quot; &amp; &#39;apostrophe&#39;'));
assert.equal(escaped.innerHTML.includes('<img'), false);
const escapedGlyph = escaped.querySelector('.theme-icon');
assert.equal(escapedGlyph.dataset.emoji, emoji);
context.applyTheme('minimal');
assert.ok(escapedGlyph.innerHTML.includes('#icon-info'));
context.applyTheme('retro');
assert.equal(escapedGlyph.textContent, emoji);
context.applyTheme('modern');
assert.ok(escapedGlyph.innerHTML.includes('#icon-info'));

console.log('Theme tests passed (picker, default theme, icons, loading controls, selection, badges, escaping)');
