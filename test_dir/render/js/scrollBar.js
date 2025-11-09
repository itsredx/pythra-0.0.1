// web/js/customScrollBar.js

export class CustomScrollBar {
    // The constructor now receives the ID of the CONTAINER.
    constructor(containerId, options = {}) {
        this.containerElement = document.getElementById(containerId);
        // The scroll target is the direct child of the container.
        this.scrollTarget = this.containerElement ? this.containerElement.firstElementChild : null;

        if (!this.scrollTarget) {
            console.error(`[CustomScrollBar] Container '${containerId}' found, but has no child element to scroll.`);
            return;
        }

        this.options = {
            thickness: 8,
            trackColor: 'rgba(0, 0, 0, 0.1)',
            thumbColor: 'rgba(0, 0, 0, 0.4)',
            radius: 4,
            ...options
        };

        this.isDragging = false;
        this.dragStartY = 0;
        this.initialScrollTop = 0;

        // Bind methods
        this._update = this._update.bind(this);
        this._handleMouseDown = this._handleMouseDown.bind(this);
        this._handleMouseMove = this._handleMouseMove.bind(this);
        this._handleMouseUp = this._handleMouseUp.bind(this);

        this._setupElements();
        this._setupEvents();
        this._update();
    }

    _setupElements() {
        // Create the track and thumb. The CSS will style them correctly.
        this.track = document.createElement('div');
        this.track.className = 'pythra-scrollbar-track-y'; // Class name is styled by the parent's CSS
        
        this.thumb = document.createElement('div');
        this.thumb.className = 'pythra-scrollbar-thumb-y';

        this.track.appendChild(this.thumb);
        // Append the track to the CONTAINER element.
        this.containerElement.appendChild(this.track);
    }

    _setupEvents() {
        this.scrollTarget.addEventListener('scroll', this._update);
        this.thumb.addEventListener('mousedown', this._handleMouseDown);
        
        this.resizeObserver = new ResizeObserver(this._update);
        this.resizeObserver.observe(this.scrollTarget);
    }

    _update() {
        const { scrollHeight, clientHeight, scrollTop } = this.scrollTarget;

        if (scrollHeight <= clientHeight) {
            this.track.style.display = 'none';
            return;
        }
        
        this.track.style.display = 'block';

        const thumbHeight = Math.max(20, (clientHeight / scrollHeight) * clientHeight); // Add min height for thumb
        const thumbPosition = (scrollTop / scrollHeight) * clientHeight;

        this.thumb.style.height = `${thumbHeight}px`;
        this.thumb.style.top = `${thumbPosition}px`;
    }

    _handleMouseDown(e) {
        e.preventDefault();
        e.stopPropagation();
        this.isDragging = true;
        this.dragStartY = e.clientY;
        // --- FIX IS HERE ---
        this.initialScrollTop = this.scrollTarget.scrollTop;

        document.addEventListener('mousemove', this._handleMouseMove);
        document.addEventListener('mouseup', this._handleMouseUp);
        document.body.style.userSelect = 'none';
    }

    _handleMouseMove(e) {
        if (!this.isDragging) return;
        e.preventDefault();
        const deltaY = e.clientY - this.dragStartY;
        // --- AND FIX IS HERE ---
        const scrollRatio = this.scrollTarget.scrollHeight / this.scrollTarget.clientHeight;
        this.scrollTarget.scrollTop = this.initialScrollTop + deltaY * scrollRatio;
    }

    _handleMouseUp(e) {
        if (!this.isDragging) return;
        this.isDragging = false;
        document.removeEventListener('mousemove', this._handleMouseMove);
        document.removeEventListener('mouseup', this._handleMouseUp);
        document.body.style.userSelect = '';
    }

    destroy() {
        this.scrollTarget.removeEventListener('scroll', this._update);
        this.resizeObserver.disconnect();
        if (this.track && this.track.parentElement) {
            this.track.parentElement.removeChild(this.track);
        }
    }
}