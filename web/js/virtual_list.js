/**
 * PythraVirtualList: A client-side engine for virtual scrolling. (Final Version)
 *
 * This engine creates its own SimpleBar instance to avoid race conditions.
 * It handles pre-rendered initial items (HTML and CSS) for an instant first paint.
 * It asynchronously fetches additional items from Python as the user scrolls.
 * Most importantly, it dynamically attaches event listeners to both pre-rendered
 * and asynchronously loaded content to ensure full interactivity.
 */
export class PythraVirtualList {
    constructor(elementId, options) {
        this.container = document.getElementById(elementId);
        if (!this.container) {
            console.error(`VirtualList Error: Container element #${elementId} not found.`);
            return;
        }

        console.log(`✅ PythraVirtualList engine is initializing for #${elementId}`);
        
        this.options = options;
        this.simplebar = new SimpleBar(this.container, this.options.simplebarOptions || {});
        this.scrollEl = this.simplebar.getScrollElement();
        this.contentEl = this.simplebar.getContentElement();
        
        this.itemCache = {}; // Cache will ONLY store HTML strings.
        this.visibleItemElements = [];

        // Process the initialItems object from Python.
        if (this.options.initialItems) {
            const initialCss = new Set();
            for (const index in this.options.initialItems) {
                const itemData = this.options.initialItems[index];
                // 1. Store ONLY the HTML string in the cache.
                this.itemCache[index] = itemData.html;
                // 2. Collect all unique CSS rules.
                if (itemData.css) {
                    initialCss.add(itemData.css);
                }
            }
            // 3. Inject all collected CSS into the dynamic stylesheet in one go.
            if (initialCss.size > 0) {
                const styleSheet = document.getElementById('dynamic-styles');
                if (styleSheet) {
                    styleSheet.textContent += `\n${[...initialCss].join('\n')}`;
                }
            }
        }

        // Setup DOM for virtualization
        this.sizer = document.createElement('div');
        this.sizer.style.position = 'absolute';
        this.sizer.style.top = '0';
        this.sizer.style.left = '0';
        this.sizer.style.width = '1px';
        this.sizer.style.height = `${this.options.itemCount * this.options.itemExtent}px`;
        this.contentEl.appendChild(this.sizer);
        this.contentEl.style.position = 'relative';

        this.render = this.render.bind(this);
        this.scrollEl.addEventListener('scroll', this.render);
        
        this.render();
    }

    /**
     * Scans a newly rendered HTML fragment and attaches reliable event listeners
     * to elements that have an inline `onclick` attribute from the Python side.
     * @param {HTMLElement} element - The container element whose children to scan (e.g., the recycled list item div).
     */
    attachEventListeners(element) {
        const clickableElements = element.querySelectorAll('[onclick]');
        clickableElements.forEach(clickable => {
            const onclickAttr = clickable.getAttribute('onclick');
            
            // Regex to parse out the callback name from "handleClick('callback_name')"
            const match = onclickAttr.match(/handleClick\('([^']+)'\)/);

            if (match && match[1]) {
                const callbackName = match[1];
                // 1. Remove the inline attribute, as it's now redundant and less reliable.
                clickable.removeAttribute('onclick');
                // 2. Add a proper, trusted event listener.
                clickable.addEventListener('click', () => {
                    if (window.pywebview && typeof handleClick === 'function') {
                        // 3. Call the global handleClick function that communicates with Python.
                        handleClick(callbackName);
                    }
                });
            }
        });
    }

    render() {
        const scrollTop = this.scrollEl.scrollTop;
        const viewportHeight = this.scrollEl.clientHeight;

        const startIndex = Math.max(0, Math.floor(scrollTop / this.options.itemExtent));
        const endIndex = Math.min(
            this.options.itemCount - 1,
            Math.ceil((scrollTop + viewportHeight) / this.options.itemExtent)
        );
        
        const itemsToRender = [];
        for (let i = startIndex; i <= endIndex; i++) {
            itemsToRender.push({ index: i, top: i * this.options.itemExtent });
        }
        
        for (let i = 0; i < itemsToRender.length; i++) {
            const item = itemsToRender[i];
            let el = this.visibleItemElements[i];

            if (!el) {
                el = document.createElement('div');
                el.style.position = 'absolute';
                el.style.width = '100%';
                el.style.height = `${this.options.itemExtent}px`;
                el.style.left = '0';
                this.contentEl.appendChild(el);
                this.visibleItemElements.push(el);
            }

            el.style.transform = `translateY(${item.top}px)`;
            
            if (el.dataset.index !== String(item.index)) {
                el.dataset.index = item.index;
                
                if (this.itemCache[item.index]) {
                    // Item was pre-rendered or fetched before.
                    el.innerHTML = this.itemCache[item.index];
                    // IMPORTANT: We must re-attach listeners every time we set innerHTML.
                    this.attachEventListeners(el);
                } else {
                    // Item needs to be fetched from Python.
                    el.innerHTML = '<div>Loading...</div>';
                    if (window.pywebview && this.options.itemBuilderName) {
                        window.pywebview.build_list_item(this.options.itemBuilderName, item.index)
                            .then(response => {
                                const { html, css } = response;
                                this.itemCache[item.index] = html;

                                if (css) {
                                    const styleSheet = document.getElementById('dynamic-styles');
                                    if (styleSheet && !styleSheet.textContent.includes(css)) {
                                        styleSheet.textContent += `\n${css}`;
                                    }
                                }
                                
                                if (el.dataset.index === String(item.index)) {
                                    el.innerHTML = html;
                                    // Attach event listeners to the newly created DOM nodes.
                                    this.attachEventListeners(el);
                                }
                            })
                            .catch(e => {
                                console.error(`Error building virtual item ${item.index}:`, e);
                                if (el.dataset.index === String(item.index)) {
                                    el.innerHTML = '<div>Error</div>';
                                }
                            });
                    }
                }
            }
        }
        
        for (let i = itemsToRender.length; i < this.visibleItemElements.length; i++) {
            this.visibleItemElements[i].style.transform = 'translateY(-9999px)';
        }
    }

    /**
     * Called from Python when the underlying data for the list has changed.
     * Clears the cache and forces a re-render of all visible items.
     */
    refresh() {
        console.log(`Refreshing ALL visible items for #${this.container.id}`);
        // 1. Clear the entire HTML cache.
        this.itemCache = {};
        
        // 2. Mark all currently visible DOM elements as "dirty" by resetting their data-index.
        this.visibleItemElements.forEach(el => {
            el.dataset.index = '-1'; // Set to an invalid index
        });
        
        // 3. Trigger a render to fetch the new, updated content.
        this.render();
    }

    /**
     * Refreshes specific items by their indices. Highly efficient.
     * @param {Array<number>} indices - An array of item indices to refresh.
     */
    refreshItems(indices) {
        if (!Array.isArray(indices)) return;
        console.log(`Refreshing specific items for #${this.container.id}:`, indices);

        indices.forEach(index => {
            // 1. Invalidate the cache for this specific item.
            if (this.itemCache[index]) {
                delete this.itemCache[index];
            }
            
            // 2. Find if this item is currently visible in the DOM.
            const visibleElement = this.visibleItemElements.find(el => el.dataset.index === String(index));
            
            if (visibleElement) {
                // 3. If it's visible, mark it as dirty so the next render pass will update it.
                visibleElement.dataset.index = '-1';
            }
        });

        // 4. Trigger a render pass to update any newly dirtied elements.
        this.render();
    }
    
    // --- END OF NEW LOGIC ---

    destroy() {
        if (this.simplebar && typeof this.simplebar.unMount === 'function') {
            this.simplebar.unMount();
        }
    }
}