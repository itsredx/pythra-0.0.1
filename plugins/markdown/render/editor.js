// PythraMarkdownEditor - A full-featured, self-contained WYSIWYG Editor Engine
class PythraMarkdownEditor {
    constructor(element, options = {}) {
        this.container = element;
        this.options = options;
        this.options.showControls = this.options.showControls ?? true;
        this.editorElement = null;
        this._changeTimer = null;

        if (!window._pythraEditorStylesInjected) {
            this.injectStyles();
            window._pythraEditorStylesInjected = true;
        }

        this.init();
    }

    init() {
        this.container.innerHTML = '';
        this.container.classList.add('pythra-editor-wrapper');

        if (this.options.showControls) {
            const toggleBtn = document.createElement('button');
            toggleBtn.id = `toggleControls_${this.options.instanceId || ''}`;
            toggleBtn.className = 'pythra-toggle-button';
            toggleBtn.textContent = 'Hide Controls';
            this.container.appendChild(toggleBtn);

            const controlPanel = this.createControlPanel();
            this.container.appendChild(controlPanel);

            toggleBtn.addEventListener('click', () => {
                const isHidden = controlPanel.classList.toggle('hidden');
                toggleBtn.textContent = isHidden ? 'Show Controls' : 'Hide Controls';
            });
        }

        const editorEl = document.createElement('div');
        editorEl.id = this.options.instanceId ? `editor_${this.options.instanceId}` : 'editor';
        editorEl.contentEditable = true;
        this.container.appendChild(editorEl);
        this.editorElement = editorEl;

        if (this.options.initialContent) {
            this.editorElement.innerHTML = this.options.initialContent;
        }

        this._setupChangeHandler();
        this._setupVisualFeedbackHandlers();
    }

    createControlPanel() {
        const panel = document.createElement('div');
        panel.id = `controlPanel_${this.options.instanceId || ''}`;
        panel.className = 'control-panel';

        const group1 = document.createElement('div');
        group1.className = 'control-group';
        [
            { cmd: 'formatBlock', val: 'H1', title: 'Heading 1', label: 'H1' },
            { cmd: 'formatBlock', val: 'H2', title: 'Heading 2', label: 'H2' },
            { cmd: 'formatBlock', val: 'P', title: 'Paragraph', label: 'P' },
            { cmd: 'insertUnorderedList', title: 'Unordered List', label: 'UL' },
            { cmd: 'insertOrderedList', title: 'Ordered List', label: 'OL' },
        ].forEach(c => group1.appendChild(this.createButton(c.cmd, c.label, c.title, c.val)));
        panel.appendChild(group1);

        const group2 = document.createElement('div');
        group2.className = 'control-group';
        [
            { id: `btn-bold_${this.options.instanceId}`, cmd: 'bold', title: 'Bold', label: '<b>B</b>' },
            { id: `btn-italic_${this.options.instanceId}`, cmd: 'italic', title: 'Italic', label: '<i>I</i>' },
            { id: `btn-underline_${this.options.instanceId}`, cmd: 'underline', title: 'Underline', label: '<u>U</u>' },
            { id: `btn-strikeThrough_${this.options.instanceId}`, cmd: 'strikeThrough', title: 'Strikethrough', label: '<s>S</s>' },
        ].forEach(c => group2.appendChild(this.createButton(c.cmd, c.label, c.title, null, c.id)));
        panel.appendChild(group2);

        const group3 = document.createElement('div');
        group3.className = 'control-group';
        group3.appendChild(this.createColorPicker());
        group3.appendChild(this.createFontSelector());
        panel.appendChild(group3);

        return panel;
    }
    
    createButton(command, label, title, value = null, id = null) {
        const button = document.createElement('button');
        if (id) button.id = id;
        button.title = title;
        button.innerHTML = label;
        button.onclick = () => window.executeCommand(command, value, this.editorElement);
        return button;
    }

    createColorPicker() {
        const input = document.createElement('input');
        input.type = 'color';
        input.title = 'Font Color';
        input.oninput = (e) => window.executeCommand('foreColor', e.target.value, this.editorElement);
        return input;
    }

    createFontSelector() {
        const wrapper = document.createElement('div');
        wrapper.className = 'font-selector-wrapper';

        const select = document.createElement('select');
        select.title = 'Font Family';
        select.onchange = (e) => window.executeCommand('fontName', e.target.value, this.editorElement);
        
        const systemFontStack = `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`;
        const defaultFonts = [
            { val: systemFontStack, label: 'System Default' },
            { val: 'Arial, sans-serif', label: 'Arial' },
            { val: 'Verdana, sans-serif', label: 'Verdana' },
            { val: "'Times New Roman', serif", label: 'Times New Roman' },
            { val: 'Georgia, serif', label: 'Georgia' },
            { val: "'Courier New', monospace", label: 'Courier New' },
        ];
        
        defaultFonts.forEach(font => select.add(new Option(font.label, font.val)));
        wrapper.appendChild(select);
        
        // --- NEW: Add a button to load system fonts ---
        if ('queryLocalFonts' in window) {
            const loadFontsBtn = this.createButton(null, '&#x1F5D8;', 'Load System Fonts');
            loadFontsBtn.style.padding = '0.5rem';
            loadFontsBtn.onclick = async () => {
                try {
                    const availableFonts = await window.queryLocalFonts();
                    // Clear existing options except the default
                    select.innerHTML = '';
                    select.add(new Option('System Default', systemFontStack));

                    // Use a Set to avoid duplicate font names
                    const fontNames = new Set();
                    for (const fontData of availableFonts) {
                        fontNames.add(fontData.family);
                    }

                    // Populate the dropdown
                    for (const name of [...fontNames].sort()) {
                        select.add(new Option(name, name));
                    }
                    loadFontsBtn.style.display = 'none'; // Hide button after success
                } catch (err) {
                    console.error('Font access denied or failed.', err);
                    loadFontsBtn.title = 'Font access was denied.';
                    loadFontsBtn.disabled = true;
                }
            };
            wrapper.appendChild(loadFontsBtn);
        }

        return wrapper;
    }

    _setupChangeHandler() {
        this.editorElement.addEventListener('input', () => {
            clearTimeout(this._changeTimer);
            this._changeTimer = setTimeout(() => {
                const content = this.editorElement.innerHTML;
                if (window.pywebview && this.options.callback) {
                    window.pywebview.on_input_changed(this.options.callback, content);
                }
            }, 180);
        });
    }

    _setupVisualFeedbackHandlers() {
        ['keyup', 'mouseup', 'focus', 'click'].forEach(eventType => {
            this.editorElement.addEventListener(eventType, () => this.updateButtonStates());
        });
    }

    updateButtonStates() {
        ['bold', 'italic', 'underline', 'strikeThrough'].forEach(command => {
            const button = document.getElementById(`btn-${command}_${this.options.instanceId}`);
            if (!button) return;
            try {
                button.classList.toggle('active', document.queryCommandState(command));
            } catch (e) {}
        });
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.id = 'pythra-editor-styles';
        style.textContent = `
            :root{--pe-color-primary:#007aff;--pe-color-primary-dark:#005bb5;--pe-color-surface:#ffffff;--pe-color-border:#dee2e6;--pe-color-text:#212529;--pe-color-text-muted:#6c757d;--pe-font-stack:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;--pe-border-radius:6px;}
            .pythra-editor-wrapper{max-width:100%;margin:2rem auto;background:var(--pe-color-surface);border:1px solid var(--pe-color-border);border-radius:var(--pe-border-radius);box-shadow:0 4px 12px rgba(0,0,0,0.05);}
            .pythra-editor-wrapper [contenteditable]{font-family:var(--pe-font-stack);min-height:100%;border-top:1px solid var(--pe-color-border);padding:1.5rem;line-height:1.7;outline:none;transition:border-color 0.2s ease,box-shadow 0.2s ease}
            .pythra-editor-wrapper [contenteditable]:focus{border-color:var(--pe-color-primary) !important;box-shadow:0 0 0 3px rgba(0,122,255,0.25)}
            .pythra-editor-wrapper [contenteditable]:empty:before{content:"Start writing...";color:var(--pe-color-text-muted);font-style:italic}
            .pythra-editor-wrapper .pythra-toggle-button{width:calc(100% + 2px);margin:-1px -1px 0 -1px;padding:0.75rem;font-size:1rem;font-weight:600;color:white;background-color:var(--pe-color-primary);border:none;border-radius:var(--pe-border-radius) var(--pe-border-radius) 0 0;cursor:pointer;transition:background-color 0.2s ease;}
            .pythra-editor-wrapper .pythra-toggle-button:hover{background-color:var(--pe-color-primary-dark)}
            .control-panel{background:#f1f3f5;padding:1rem;display:flex;flex-direction:column;gap:1rem;transition:all 0.3s ease-in-out;max-height:1000px;opacity:1;overflow:hidden;}
            .control-panel.hidden{max-height:0;padding-top:0;padding-bottom:0;margin-top:-1px;opacity:0;border:1px solid transparent}
            .control-group{display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center}
            .control-panel button,.control-panel select,.control-panel input[type="color"]{font-family:var(--pe-font-stack);font-size:0.9rem;padding:0.5rem 0.75rem;background:var(--pe-color-surface);border:1px solid var(--pe-color-border);border-radius:var(--pe-border-radius);cursor:pointer;transition:background-color 0.2s ease,border-color 0.2s ease, box-shadow 0.2s ease;}
            .control-panel button:hover,.control-panel select:hover{background:#e9ecef}
            .control-panel button.active{background-color:var(--pe-color-primary);color:white;border-color:var(--pe-color-primary-dark)}
            // .control-panel select{-webkit-appearance:none;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath fill='none' stroke='%23343a40' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 0.5rem center;background-size:1em;padding-right:2rem;}
            // .control-panel select:focus{border-color:var(--pe-color-primary);box-shadow:0 0 0 3px rgba(0,122,255,0.25);background-color:var(--pe-color-surface);}
            .control-panel input[type="color"]{padding:0.25rem;height:38px;min-width:40px;border:1px solid var(--pe-color-border);background:transparent}
            .font-selector-wrapper{display:flex;gap:0.5rem;align-items:center;}
            .pythra-editor-wrapper [contenteditable] h1,h2,h3,h4,h5,p,ul,ol{margin:1em 0}
            .pythra-editor-wrapper [contenteditable] ul,.pythra-editor-wrapper [contenteditable] ol{padding-left:2em}
        `;
        document.head.appendChild(style);
    }
    
    setContent(html) { if (this.editorElement) this.editorElement.innerHTML = html; }
    getContent() { return this.editorElement ? this.editorElement.innerHTML : ''; }
    focus() { if (this.editorElement) this.editorElement.focus(); }
}

// Expose the class globally
window.PythraMarkdownEditor = PythraMarkdownEditor;

// --- Global Helper Functions ---
window.executeCommand = (command, value = null, editorToFocus) => {
    if (!command) return;
    try {
        document.execCommand(command, false, value);
    } catch (err) {
        console.error(`Error executing command '${command}':`, err);
    }
    if (editorToFocus) editorToFocus.focus();
};

document.addEventListener('DOMContentLoaded', () => {
    try { document.execCommand('styleWithCSS', false, true); } 
    catch (e) { console.warn('styleWithCSS is not supported by this browser.'); }
});