"""Language identifiers shared by preferences and UI, without application imports."""

LANGUAGE_MODULES = {
    'Español': 'es',
    'English': 'en',
    'Portugues': 'pt',
    'Français': 'fr',
    'Deutsch': 'de',
    'Italiano': 'it',
    '日本語': 'ja',
    '简体中文': 'zh_cn',
    'Русский': 'ru',
}
AVAILABLE_LANGUAGES = {name: name for name in LANGUAGE_MODULES}
DEFAULT_LANGUAGE = 'Español'
