// PythraMarkdownEditor - A full-featured, self-contained, and memory-safe WYSIWYG Editor Engine
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
        this.editorElement = null;
        this._changeTimer = null;
        this._changeHandler = null;
        this._feedbackHandler = null;
        this.options.showGrid = this.options.showGrid ?? false;

        if (this.container) {
            this.container.style.width = this.options.width || '100%';
            this.container.style.height = this.options.height || 'auto';
        }

        if (!window._pythraEditorStylesInjected) {
            this.injectStyles();
            window._pythraEditorStylesInjected = true;
        }

        this.init();
    }

    init() {
        let controlPanel = this.container.querySelector('.control-panel');
        let editorEl = this.container.querySelector('[contenteditable="true"]');

        this.container.classList.add('pythra-editor-wrapper');

        if (this.options.showControls) {
            let toggleBtn = this.container.querySelector('.pythra-toggle-button');
            if (!controlPanel) {
                toggleBtn = document.createElement('button');
                toggleBtn.id = `toggleControls_${this.options.instanceId || ''}`;
                toggleBtn.className = 'pythra-toggle-button';
                // Prepend the button so it's always at the top
                this.container.prepend(toggleBtn);
                
                controlPanel = this.createControlPanel();
                // Insert after the toggle button
                toggleBtn.insertAdjacentElement('afterend', controlPanel);
            }
            
            // --- THIS IS THE FINAL FIX FOR PRESERVING HIDDEN STATE ---
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

        // --- NEW: Apply the grid class based on the option ---
        if (this.editorElement) {
            if (this.options.showGrid) {
                this.editorElement.classList.add('grid-background');
            } else {
                this.editorElement.classList.remove('grid-background');
            }
        }
        // --- END NEW LOGIC ---

        this._setupChangeHandler();
        this._setupVisualFeedbackHandlers();

        if (this.imageResizer) this.imageResizer.destroy();
        this.imageResizer = new PythraImageResizer(this.editorElement);
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

    updateButtonStates() {
        ['bold', 'italic', 'underline', 'strikeThrough'].forEach(command => {
            const button = document.getElementById(`btn-${command}_${this.options.instanceId}`);
            if (!button) return;
            try {
                button.classList.toggle('active', document.queryCommandState(command));
            } catch (e) { /* This can safely fail if editor is not focused */ }
        });
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.id = 'pythra-editor-styles';
        style.textContent = `
            :root{--pe-color-primary:#007aff;--pe-color-primary-dark:#005bb5;--pe-color-surface:#ffffff;--pe-color-border:#dee2e6;--pe-color-text:#212529;--pe-color-text-muted:#6c757d;--pe-font-stack:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;--pe-border-radius:6px;}
            .pythra-editor-wrapper{box-sizing:border-box;display:flex;flex-direction:column;background:var(--pe-color-surface);border:1px solid var(--pe-color-border);border-radius:var(--pe-border-radius);box-shadow:0 4px 12px rgba(0,0,0,0.05);}
            .pythra-editor-wrapper [contenteditable]{font-family:var(--pe-font-stack);flex-grow:1;min-height:150px;border-top:1px solid var(--pe-color-border);padding:1.5rem;line-height:1.7;outline:none;overflow-y:auto;}
            .pythra-editor-wrapper [contenteditable]:focus{border-color:var(--pe-color-primary) !important;box-shadow:0 0 0 3px rgba(0,122,255,0.25)}
            .pythra-editor-wrapper [contenteditable]:empty:before{content:"Start writing...";color:var(--pe-color-text-muted);font-style:italic}
            .pythra-editor-wrapper .pythra-toggle-button{flex-shrink:0;width:100%;padding:0.75rem;font-size:1rem;font-weight:600;color:white;background-color:var(--pe-color-primary);border:none;border-radius:var(--pe-border-radius) var(--pe-border-radius) 0 0;cursor:pointer;transition:background-color 0.2s ease;}
            .pythra-editor-wrapper .pythra-toggle-button:hover{background-color:var(--pe-color-primary-dark)}
            .control-panel{flex-shrink:0;background:#f1f3f5;padding:1rem;display:flex;flex-direction:column;gap:1rem;transition:all 0.3s ease-in-out;max-height:1000px;opacity:1;overflow:hidden;}
            .control-panel.hidden{max-height:0;padding-top:0;padding-bottom:0;opacity:0;}
            .control-group{display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center}
            .control-panel button,.control-panel select,.control-panel input[type="color"]{font-family:var(--pe-font-stack);font-size:0.9rem;padding:0.5rem 0.75rem;background:var(--pe-color-surface);border:1px solid var(--pe-color-border);border-radius:var(--pe-border-radius);cursor:pointer;transition:background-color 0.2s ease,border-color 0.2s ease, box-shadow 0.2s ease;}
            .control-panel button:hover,.control-panel select:hover{background:#e9ecef}
            .control-panel button.active{background-color:var(--pe-color-primary);color:white;border-color:var(--pe-color-primary-dark)}
            .control-panel select{-webkit-appearance:none;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath fill='none' stroke='%23343a40' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 0.5rem center;background-size:1em;padding-right:2rem;}
            .control-panel select:focus{border-color:var(--pe-color-primary);box-shadow:0 0 0 3px rgba(0,122,255,0.25);background-color:var(--pe-color-surface);}
            .control-panel input[type="color"]{padding:0.25rem;height:38px;min-width:40px;border:1px solid var(--pe-color-border);background:transparent}
            .pythra-image-resizer-wrapper{position:absolute;border:2px solid var(--pe-color-primary);pointer-events:none;}
            .pythra-resize-handle{position:absolute;width:10px;height:10px;background-color:var(--pe-color-primary);border:1px solid white;border-radius:50%;pointer-events:auto;}
            .pythra-resize-handle.top-left{top:-6px;left:-6px;cursor:nwse-resize;}
            .pythra-resize-handle.top-right{top:-6px;right:-6px;cursor:nesw-resize;}
            .pythra-resize-handle.bottom-left{bottom:-6px;left:-6px;cursor:nesw-resize;}
            .pythra-resize-handle.bottom-right{bottom:-6px;right:-6px;cursor:nwse-resize;}
            /* --- NEW: CSS for the dotted grid background --- */
            .pythra-editor-wrapper [contenteditable].grid-background {
                /* Creates a repeating pattern of dots */
                background-image: radial-gradient(circle, #D3D3D3 1px, rgba(0,0,0,0) 1px);
                background-size: 20px 20px; /* Adjust these values to change dot spacing */
            }
        `;
        document.head.appendChild(style);
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
        // Append to editor's parent to avoid contenteditable issues
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
        
        // This needs to be relative to the parent of the editor now
        const editorParent = this.editor.parentNode;
        this.editor.parentNode.style.position = this.editor.parentNode.style.position || 'relative';

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
        const dy = e.clientY - this.startPos.y;

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