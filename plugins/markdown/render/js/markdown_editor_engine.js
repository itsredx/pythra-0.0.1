// PythraMarkdownEditor Engine Definition
window.PythraMarkdownEditor = class PythraMarkdownEditor {
    constructor(container, options = {}) {
        console.log('Creating PythraMarkdownEditor instance:', options);
        this.container = container;
        this.options = options;
        this.editorElement = null;
        this._changeTimer = null;
        this.init();
    }

    init() {
        // Create editor structure
        const editorEl = document.createElement('div');
        editorEl.id = 'editor';
        editorEl.contentEditable = true;
        editorEl.className = 'editor-content';
        editorEl.style.cssText = 'width:100%;height:100%;padding:10px;box-sizing:border-box;border:1px solid #ccc;outline:none;overflow-y:auto;';
        
        // Clear container and add editor
        this.container.innerHTML = '';
        this.container.appendChild(editorEl);
        this.editorElement = editorEl;

        // Setup change handler
        this._setupChangeHandler();

        console.log('Editor initialized:', {
            container: this.container,
            editor: this.editorElement,
            options: this.options
        });
    }

    _setupChangeHandler() {
        if (!this.editorElement) return;
        
        this.editorElement.addEventListener('input', () => {
            clearTimeout(this._changeTimer);
            this._changeTimer = setTimeout(() => {
                if (window.pywebview && this.options.callback) {
                    window.pywebview.on_input_changed(this.options.callback, this.editorElement.innerHTML);
                }
            }, 180);
        });
    }

    execCommand(cmd, value = null) {
        if (!this.editorElement) return;
        try {
            document.execCommand(cmd, false, value);
        } catch(e) {
            console.warn('Editor command failed:', e);
        }
    }

    setContent(html) {
        if (this.editorElement) {
            this.editorElement.innerHTML = html;
        }
    }

    getContent() {
        return this.editorElement ? this.editorElement.innerHTML : '';
    }

    focus() {
        if (this.editorElement) {
            this.editorElement.focus();
        }
    }
};

// Framework initialization function
window.initEditor = function(element, options) {
    console.log('Framework calling initEditor:', { element, options });
    const editor = new PythraMarkdownEditor(element, options);
    if (options.instanceId) {
        window._pythra_instances = window._pythra_instances || {};
        window._pythra_instances[options.instanceId] = editor;
    }
    return editor;
};