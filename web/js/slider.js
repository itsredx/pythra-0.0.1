/**
 * PythraSlider: A client-side engine for handling slider interactions.
 * This is now a proper JavaScript module class.
 */
export class PythraSlider { // <-- ADD 'export' HERE
    constructor(elementId, options) {
        this.container = document.getElementById(elementId);
        if (!this.container) {
            console.error(`Slider container with ID #${elementId} not found.`);
            return;
        }

        console.log(`✅ PythraSlider engine is initializing for #${elementId}`);

        this.options = options;
        this.dragBool = false;
        
        // ... THE REST OF THE FILE REMAINS EXACTLY THE SAME ...
        this.track = this.container.querySelector('.slider-track');
        this.thumb = this.container.querySelector('.slider-thumb');
        
        this.handleDragStart = this.handleDragStart.bind(this);
        this.handleDragMove = this.handleDragMove.bind(this);
        this.handleDragEnd = this.handleDragEnd.bind(this);

        this.container.addEventListener('mousedown', this.handleDragStart);
        this.container.addEventListener('touchstart', this.handleDragStart, { passive: false });
    }

    handleDragStart(event) {
        event.preventDefault();
        this.container.classList.add('active');
        
        document.addEventListener('mousemove', this.handleDragMove);
        document.addEventListener('mouseup', this.handleDragEnd);
        document.addEventListener('touchmove', this.handleDragMove);
        document.addEventListener('touchend', this.handleDragEnd);


        this.updatePosition(event);
    }

    handleDragMove(event) {
        this.updatePosition(event);
    }

    handleDragEnd(event) {
        this.container.classList.remove('active');
        
        document.removeEventListener('mousemove', this.handleDragMove);
        document.removeEventListener('mouseup', this.handleDragEnd);
        document.removeEventListener('touchmove', this.handleDragMove);
        document.removeEventListener('touchend', this.handleDragEnd);
        // console.log("drag ended")
        this.dragBool = true;
        console.log("drag ended", this.dragBool, event);
        this.updatePosition(event);
    }

    updatePosition(event) {
        if (!this.track) return;
        const rect = this.track.getBoundingClientRect();
        const clientX = event.touches ? event.touches[0].clientX : event.clientX;
        
        let positionX = clientX - rect.left;
        let percentage = (positionX / rect.width) * 100;
        
        percentage = Math.max(0, Math.min(100, percentage));
        
        this.container.style.setProperty('--slider-percentage', `${percentage}%`);
        console.log(percentage, this.options.onDragName);
        
        const range = this.options.max - this.options.min;
        const newValue = this.options.min + (percentage / 100) * range;
        console.log(percentage, this.options.onDragName, newValue);
        
        if (window.pywebview && this.options.onDragName) {
            window.pywebview.on_drag_update(this.options.onDragName, newValue, this.dragBool);
        }
        if (this.dragBool){
            console.log("hasDrag: Ended")
            this.dragBool = false
        } else {
            console.log("dragging")
        }
    }

    destroy() {
        if (!this.container) return;
        this.container.removeEventListener('mousedown', this.handleDragStart);
        this.container.removeEventListener('touchstart', this.handleDragStart);
        this.handleDragEnd();
    }
}