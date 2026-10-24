// TI-ConnectMC: gives the tab icon, the home-screen/desktop app icon and the
// install manifest the look of the user's default theme ("Set as default" in
// Settings). Loaded in <head> after the icon links, so the right icon is
// linked before the browser asks for it. The icons are made by
// themes/tools/make_icons.py; the Minecraft set lives at the site root.
(function () {
    'use strict';

    const DEFAULT_THEME_KEY = 'webtilp.theme';
    const ICON_SETS = {
        'minecraft': 'minecraft',
        'minecraft-day': 'minecraft',
        'minecraft-night': 'minecraft',
        'modern': 'modern',
        'cyberpunk': 'cyberpunk',
        'dark-modern': 'aurora',
        'light-modern': 'aurora',
        'retro': 'retro',
        'professional-light': 'professional',
        'professional-dark': 'professional',
        'minimal': 'minimal'
    };

    function iconFolder(themeId) {
        const set = ICON_SETS[themeId] || 'minecraft';
        return set === 'minecraft' ? '' : `themes/icons/${set}/`;
    }

    // Every icon set uses the root file names, so only the folder changes.
    function applyAppIcon(themeId) {
        const folder = iconFolder(themeId);
        document.querySelectorAll('link[rel="icon"], link[rel="apple-touch-icon"], link[rel="manifest"]').forEach(link => {
            link.dataset.file ||= link.getAttribute('href').split('/').pop();
            const href = folder + link.dataset.file;
            if (link.getAttribute('href') !== href) {
                link.setAttribute('href', href);
            }
        });
    }

    let defaultTheme = null;
    try {
        defaultTheme = localStorage.getItem(DEFAULT_THEME_KEY);
    } catch {
        // Storage blocked: keep the Minecraft icons.
    }
    applyAppIcon(defaultTheme);
    globalThis.TIConnectMCAppIcon = { apply: applyAppIcon };
})();
