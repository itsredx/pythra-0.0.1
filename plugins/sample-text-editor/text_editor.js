/**
 * TextEditor Widget - PyThra JavaScript Component
 * 
 * This is a sample JavaScript widget component that demonstrates
 * the new package system integration.
 */

class TextEditorWidget {
    constructor(element, props = {}) {
        this.element = element;
        this.props = {
            placeholder: 'Enter text here...',
            multiline: true,
            readonly: false,
            ...props
        };
        
        this.init();
    }
    
    init() {
        // Create the textarea element
        this.textarea = document.createElement(this.props.multiline ? 'textarea' : 'input');
        
        if (!this.props.multiline) {
            this.textarea.type = 'text';
        }
        
        this.textarea.placeholder = this.props.placeholder;
        this.textarea.readOnly = this.props.readonly;
        this.textarea.className = 'pythra-text-editor';
        
        // Add some basic styling
        this.textarea.style.cssText = `
            width: 100%;
            min-height: 200px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            resize: vertical;
            outline: none;
        `;
        
        // Add focus styling
        this.textarea.addEventListener('focus', () => {
            this.textarea.style.borderColor = '#0066cc';
            this.textarea.style.boxShadow = '0 0 0 2px rgba(0, 102, 204, 0.2)';
        });
        
        this.textarea.addEventListener('blur', () => {
            this.textarea.style.borderColor = '#ddd';
            this.textarea.style.boxShadow = 'none';
        });
        
        // Add to DOM
        this.element.appendChild(this.textarea);
    }
    
    getValue() {
        return this.textarea.value;
    }
    
    setValue(value) {
        this.textarea.value = value;
    }
    
    focus() {
        this.textarea.focus();
    }
    
    destroy() {
        if (this.textarea) {
            this.textarea.remove();
        }
    }
}

// Export for PyThra framework
window.TextEditorWidget = TextEditorWidget;