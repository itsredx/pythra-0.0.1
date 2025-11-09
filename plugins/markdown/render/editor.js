// PythraMarkdownEditor - A full-featured, themeable, and memory-safe WYSIWYG Editor Engine
class PythraMarkdownEditor {
    constructor(elementOrId, options = {}) {
        if (typeof elementOrId === 'string') {
            this.container = document.getElementById(elementOrId);
            if (!this.container) {
                console.error(`PythraMarkdownEditor Error: Container with ID '${elementOrId}' not found.`);
                return;
            }
        } else {
            this.container = elementOrId;
        }

        this.options = options;
        this.options.showControls = this.options.showControls ?? true;
        this.options.showGrid = this.options.showGrid ?? false;
        
        this.editorElement = null;
        this._changeTimer = null;
        this._changeHandler = null;
        this._feedbackHandler = null;

        if (this.container) {
            this.container.style.width = this.options.width || (this.options.style?.defaults?.width || '100%');
            this.container.style.height = this.options.height || (this.options.style?.defaults?.height || 'auto');
        }

        if (!window._pythraEditorStylesInjected) {
            this.injectStyles();
            window._pythraEditorStylesInjected = true;
        }

        // --- NEW: Apply the dynamic styles from Python ---
        this._applyStyles();

        this.init();
    }
    
    // --- NEW METHOD: Applies styles from options as CSS variables ---
    _applyStyles() {
        if (!this.options.style || !this.container) return;

        const style = this.options.style;
        const root = this.container; // Set variables on the component's root element

        const setVar = (name, value) => value && root.style.setProperty(name, value);

        // Theme styles
        if (style.theme) {
            setVar('--pe-accent-color', style.theme.accentColor);
            setVar('--pe-accent-hover', style.theme.accentHover);
            setVar('--pe-border-color', style.theme.borderColor);
            setVar('--pe-border-radius', style.theme.borderRadius);
            setVar('--pe-border-width', style.theme.borderWidth);
            if (style.theme.focusRing) {
                setVar('--pe-focus-ring-color', style.theme.focusRing.color);
                setVar('--pe-focus-ring-width', style.theme.focusRing.width);
            }
        }
        
        // Toolbar styles
        if (style.toolbar) {
            setVar('--pe-toolbar-bg', style.toolbar.backgroundColor);
            setVar('--pe-toolbar-hover', style.toolbar.hoverColor);
            setVar('--pe-toolbar-active', style.toolbar.activeColor);
            setVar('--pe-toolbar-icon', style.toolbar.iconColor);
            setVar('--pe-toolbar-shadow', style.toolbar.shadow);
        }
        
        // Content area styles
        if (style.content) {
            setVar('--pe-content-bg', style.content.backgroundColor);
            setVar('--pe-content-text', style.content.textColor);
            setVar('--pe-content-font', style.content.fontFamily);
            setVar('--pe-content-font-size', style.content.fontSize);
            setVar('--pe-content-line-height', style.content.lineHeight);
            setVar('--pe-content-padding', style.content.padding);
            setVar('--pe-content-placeholder', style.content.placeholderColor);
        }
        
        // Grid styles
        if (style.grid) {
            setVar('--pe-grid-dot-color', style.grid.dotColor);
            setVar('--pe-grid-dot-size', `${style.grid.dotSize || 1}px`);
            setVar('--pe-grid-dot-spacing', `${style.grid.dotSpacing || 20}px`);
        }
    }

    init() {
        // ... The init() method and all other logic remains exactly the same ...
        // It will now benefit from the styles applied in the constructor.
        let controlPanel = this.container.querySelector('.control-panel');
        let editorEl = this.container.querySelector('[contenteditable="true"]');

        this.container.classList.add('pythra-editor-wrapper');

        if (this.options.showControls) {
            let toggleBtn = this.container.querySelector('.pythra-toggle-button');
            if (!controlPanel) {
                toggleBtn = document.createElement('button');
                toggleBtn.id = `toggleControls_${this.options.instanceId || ''}`;
                toggleBtn.className = 'pythra-toggle-button';
                this.container.prepend(toggleBtn);
                
                controlPanel = this.createControlPanel();
                toggleBtn.insertAdjacentElement('afterend', controlPanel);
            }
            
            if (this.options.controlsInitiallyHidden && !controlPanel.classList.contains('hidden')) {
                controlPanel.classList.add('hidden');
            } else if (!this.options.controlsInitiallyHidden && controlPanel.classList.contains('hidden')) {
                controlPanel.classList.remove('hidden');
            }
            
            if (toggleBtn) {
                const isHidden = controlPanel.classList.contains('hidden');
                toggleBtn.textContent = isHidden ? 'Show Controls' : 'Hide Controls';
                toggleBtn.onclick = () => {
                    const isNowHidden = controlPanel.classList.toggle('hidden');
                    toggleBtn.textContent = isNowHidden ? 'Show Controls' : 'Hide Controls';
                    if (typeof handleInput === 'function' && this.options.onToggleControlsCallback) {
                        handleInput(this.options.onToggleControlsCallback, !isNowHidden);
                    }
                };
            }
        } else if (controlPanel) {
            const toggleBtn = this.container.querySelector('.pythra-toggle-button');
            if (toggleBtn) toggleBtn.remove();
            controlPanel.remove();
        }

        if (!editorEl) {
            editorEl = document.createElement('div');
            editorEl.id = this.options.instanceId ? `editor_${this.options.instanceId}` : 'editor';
            editorEl.contentEditable = true;
            this.container.appendChild(editorEl);
        }
        this.editorElement = editorEl;

        if (this.options.initialContent && this.editorElement.innerHTML !== this.options.initialContent) {
            this.editorElement.innerHTML = this.options.initialContent;
        }

        if (this.editorElement) {
            this.editorElement.classList.toggle('grid-background', this.options.showGrid);
        }

        this._setupChangeHandler();
        this._setupVisualFeedbackHandlers();

        if (this.imageResizer) this.imageResizer.destroy();
        this.imageResizer = new PythraImageResizer(this.editorElement);
    }

    // ... createControlPanel, createButton, etc. are all correct ...

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
        
        const group4 = document.createElement('div');
        group4.className = 'control-group';
        const insertImageBtn = this.createButton('insertImage', '🖼️', 'Insert Image');
        insertImageBtn.onclick = () => {
            const url = prompt("Enter the image URL:");
            if (url) {
                this.execCommand('insertImage', url);
            }
        };
        group4.appendChild(insertImageBtn);
        panel.appendChild(group4);

        return panel;
    }

    createButton(command, label, title, value = null, id = null) {
        const button = document.createElement('button');
        if (id) button.id = id;
        button.title = title;
        button.innerHTML = label;
        button.onclick = () => this.execCommand(command, value);
        return button;
    }

    createColorPicker() {
        const input = document.createElement('input');
        input.type = 'color';
        input.title = 'Font Color';
        input.oninput = (e) => this.execCommand('foreColor', e.target.value);
        return input;
    }

    createFontSelector() {
        const select = document.createElement('select');
        select.title = 'Font Family';
        select.onchange = (e) => this.execCommand('fontName', e.target.value);

        const fontsToUse = (this.options.fontList && Array.isArray(this.options.fontList) && this.options.fontList.length > 0)
            ? this.options.fontList
            : [ 
                { val: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif', label: 'System Default' },
                { val: 'Arial, sans-serif', label: 'Arial' },
                { val: "'Times New Roman', serif", label: 'Times New Roman' },
              ];
        
        fontsToUse.forEach(font => select.add(new Option(font.label, font.val)));
        return select;
    }

    _setupChangeHandler() {
        if (!this.editorElement) return;
        this._changeHandler = () => {
            clearTimeout(this._changeTimer);
            this._changeTimer = setTimeout(() => {
                const content = this.editorElement.innerHTML;
                if (typeof handleInput === 'function' && this.options.callback) {
                    handleInput(this.options.callback, content);
                }
            }, 180);
        };
        this.editorElement.addEventListener('input', this._changeHandler);
    }

    _setupVisualFeedbackHandlers() {
        if (!this.editorElement) return;
        this._feedbackHandler = () => this.updateButtonStates();
        ['keyup', 'mouseup', 'focus', 'click'].forEach(eventType => {
            this.editorElement.addEventListener(eventType, this._feedbackHandler);
        });
    }
    
    // --- MODIFIED: injectStyles now uses CSS variables ---
    injectStyles() {
        const style = document.createElement('style');
        style.id = 'pythra-editor-styles';
        style.textContent = `
            :root{
                --pe-accent-color: #007aff; --pe-accent-hover: #005bb5;
                --pe-border-color: #dee2e6; --pe-border-radius: 6px; --pe-border-width: 1px;
                --pe-focus-ring-color: rgba(0,122,255,0.25); --pe-focus-ring-width: 3px;
                --pe-toolbar-bg: #f1f3f5; --pe-toolbar-hover: #e9ecef; --pe-toolbar-active: #007aff; --pe-toolbar-icon: #212529;
                --pe-content-bg: #ffffff; --pe-content-text: #212529;
                --pe-content-font: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
                --pe-content-font-size: 16px; --pe-content-line-height: 1.7; --pe-content-padding: 1.5rem;
                --pe-content-placeholder: #6c757d;
                --pe-grid-dot-color: #D3D3D3; --pe-grid-dot-size: 1px; --pe-grid-dot-spacing: 20px;
            }
            .pythra-editor-wrapper{box-sizing:border-box;display:flex;flex-direction:column;background:var(--pe-content-bg);border:var(--pe-border-width) solid var(--pe-border-color);border-radius:var(--pe-border-radius);box-shadow:0 4px 12px rgba(0,0,0,0.05);}
            .pythra-editor-wrapper [contenteditable]{color: var(--pe-content-text); font-family:var(--pe-content-font); font-size: var(--pe-content-font-size); line-height: var(--pe-content-line-height); padding: var(--pe-content-padding); flex-grow:1;min-height:150px;border-top:1px solid var(--pe-border-color);outline:none;overflow-y:auto;}
            .pythra-editor-wrapper [contenteditable]:focus{border-color:var(--pe-accent-color) !important;box-shadow:0 0 0 var(--pe-focus-ring-width) var(--pe-focus-ring-color)}
            .pythra-editor-wrapper [contenteditable]:empty:before{content:"Start writing...";color:var(--pe-content-placeholder);font-style:italic}
            .pythra-editor-wrapper .pythra-toggle-button{flex-shrink:0;width:100%;padding:0.75rem;font-size:1rem;font-weight:600;color:white;background-color:var(--pe-accent-color);border:none;border-radius:var(--pe-border-radius) var(--pe-border-radius) 0 0;cursor:pointer;transition:background-color 0.2s ease;}
            .pythra-editor-wrapper .pythra-toggle-button:hover{background-color:var(--pe-accent-hover)}
            .control-panel{flex-shrink:0;background:var(--pe-toolbar-bg);padding:1rem;display:flex;flex-direction:column;gap:1rem;transition:all 0.3s ease-in-out;max-height:1000px;opacity:1;overflow:hidden;}
            .control-panel.hidden{max-height:0;padding-top:0;padding-bottom:0;opacity:0;}
            .control-group{display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center}
            .control-panel button,.control-panel select,.control-panel input[type="color"]{color:var(--pe-toolbar-icon); font-family:var(--pe-content-font);font-size:0.9rem;padding:0.5rem 0.75rem;background:var(--pe-content-bg);border:1px solid var(--pe-border-color);border-radius:var(--pe-border-radius);cursor:pointer;transition:all 0.2s ease;}
            .control-panel button:hover,.control-panel select:hover{background:var(--pe-toolbar-hover)}
            .control-panel button.active{background-color:var(--pe-toolbar-active);color:white;border-color:var(--pe-accent-hover)}
            .control-panel select:focus{border-color:var(--pe-accent-color);box-shadow:0 0 0 var(--pe-focus-ring-width) var(--pe-focus-ring-color);background-color:var(--pe-content-bg);}
            .pythra-image-resizer-wrapper{position:absolute;border:2px solid var(--pe-accent-color);pointer-events:none;}
            .pythra-resize-handle{position:absolute;width:10px;height:10px;background-color:var(--pe-accent-color);border:1px solid white;border-radius:50%;pointer-events:auto;}
            .pythra-editor-wrapper [contenteditable].grid-background {background-image:radial-gradient(var(--pe-grid-dot-color) var(--pe-grid-dot-size), transparent 0); background-size: var(--pe-grid-dot-spacing) var(--pe-grid-dot-spacing);}
        `;
        document.head.appendChild(style);
    }
    
    // ... (rest of the class and file are correct) ...
    updateButtonStates() {
        ['bold', 'italic', 'underline', 'strikeThrough'].forEach(command => {
            const button = document.getElementById(`btn-${command}_${this.options.instanceId}`);
            if (!button) return;
            try {
                button.classList.toggle('active', document.queryCommandState(command));
            } catch (e) { /* This can safely fail if editor is not focused */ }
        });
    }

    execCommand(command, value = null) {
        if (!command) return;
        try {
            document.execCommand(command, false, value);
        } catch (err) {
            console.error(`Error executing command '${command}':`, err);
        }
        this.editorElement.focus();
        this.updateButtonStates();
    }

    setContent(html) { if (this.editorElement) this.editorElement.innerHTML = html; }
    getContent() { return this.editorElement ? this.editorElement.innerHTML : ''; }
    focus() { if (this.editorElement) this.editorElement.focus(); }

    destroy() {
        console.log(`🔥 Destroying PythraMarkdownEditor instance: ${this.options.instanceId}`);
        
        if (this.editorElement && this._changeHandler) {
            this.editorElement.removeEventListener('input', this._changeHandler);
        }
        if (this.editorElement && this._feedbackHandler) {
            ['keyup', 'mouseup', 'focus', 'click'].forEach(eventType => {
                this.editorElement.removeEventListener(eventType, this._feedbackHandler);
            });
        }
        
        if (this.imageResizer) {
            this.imageResizer.destroy();
        }

        clearTimeout(this._changeTimer);
    }
}
// ... (rest of file)
window.PythraMarkdownEditor = PythraMarkdownEditor;

document.addEventListener("DOMContentLoaded", () => {
    try {
        document.execCommand("styleWithCSS", false, true);
    } catch (e) {
        console.warn("styleWithCSS is not supported by this browser.");
    }
});

class PythraImageResizer {
    constructor(editorElement) {
        this.editor = editorElement;
        this.selectedImage = null;
        this.wrapper = null;
        this.handles = [];

        this.handleClick = this.handleClick.bind(this);
        this.handleMouseDown = this.handleMouseDown.bind(this);
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleMouseUp = this.handleMouseUp.bind(this);
        
        this.editor.addEventListener('click', this.handleClick);
    }

    handleClick(e) {
        const target = e.target;
        if (target.tagName === 'IMG') {
            if (this.selectedImage !== target) {
                this.selectImage(target);
            }
        } else if (this.selectedImage) {
            this.deselectImage();
        }
    }
    
    selectImage(img) {
        this.deselectImage();

        this.selectedImage = img;
        
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'pythra-image-resizer-wrapper';
        this.editor.parentNode.style.position = this.editor.parentNode.style.position || 'relative';
        this.editor.parentNode.appendChild(this.wrapper);
        this.positionWrapper();
        
        const handlePositions = ['top-left', 'top-right', 'bottom-left', 'bottom-right'];
        handlePositions.forEach(pos => {
            const handle = document.createElement('div');
            handle.className = `pythra-resize-handle ${pos}`;
            handle.dataset.position = pos;
            this.wrapper.appendChild(handle);
            handle.addEventListener('mousedown', this.handleMouseDown);
        });
    }
    
    deselectImage() {
        if (this.wrapper) {
            this.wrapper.remove();
            this.wrapper = null;
        }
        this.selectedImage = null;
    }
    
    positionWrapper() {
        if (!this.selectedImage || !this.wrapper) return;
        
        const editorParent = this.editor.parentNode;
        const imgRect = this.selectedImage.getBoundingClientRect();
        const parentRect = editorParent.getBoundingClientRect();
        
        this.wrapper.style.top = `${imgRect.top - parentRect.top}px`;
        this.wrapper.style.left = `${imgRect.left - parentRect.left}px`;
        this.wrapper.style.width = `${imgRect.width}px`;
        this.wrapper.style.height = `${imgRect.height}px`;
    }

    handleMouseDown(e) {
        e.preventDefault();
        e.stopPropagation();

        this.startRect = this.selectedImage.getBoundingClientRect();
        this.startPos = { x: e.clientX, y: e.clientY };
        this.handlePosition = e.target.dataset.position;

        document.addEventListener('mousemove', this.handleMouseMove);
        document.addEventListener('mouseup', this.handleMouseUp);
    }
    
    handleMouseMove(e) {
        if (!this.startRect) return;

        const dx = e.clientX - this.startPos.x;
        let newWidth = this.startRect.width;
        
        if (this.handlePosition.includes('right')) {
            newWidth += dx;
        } else if (this.handlePosition.includes('left')) {
            newWidth -= dx;
        }

        this.selectedImage.style.width = `${Math.max(20, newWidth)}px`;
        this.selectedImage.style.height = 'auto';
        
        this.positionWrapper();
    }

    handleMouseUp() {
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseup', this.handleMouseUp);
        this.startRect = null;
        
        this.editor.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
    }

    destroy() {
        this.editor.removeEventListener('click', this.handleClick);
        this.deselectImage();
    }
}