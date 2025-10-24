// Track registered editor instances
const registeredEditors = {};

// Framework-integrated editor initialization
function initializeEditor(params) {
    const { containerId, instanceId, callbackName } = params;

    // Get container after framework has initialized DOM
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    // Initialize editor with SimpleMDE
    const editor = new SimpleMDE({
        element: container,
        spellChecker: false,
        status: false
    });

    // Store instance 
    registeredEditors[instanceId] = editor;

    // Set up change handler using framework callback name
    editor.codemirror.on('change', () => {
        const value = editor.value();
        if (window[callbackName]) {
            window[callbackName](value);
        }
    });

    return editor;
}

// Export for framework registration
window.pythraMarkdownEditor = {
    initialize: initializeEditor
};