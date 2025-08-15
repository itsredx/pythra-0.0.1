/**
 * PythraGestureDetector: A client-side engine for a feature-rich gesture detector.
 *
 * It uses Pointer Events to handle mouse and touch统一. It disambiguates between
 * taps, double taps, long presses, and panning gestures.
 */
export class PythraGestureDetector {
    constructor(elementId, options) {
        this.element = document.getElementById(elementId);
        if (!this.element) {
            console.error(`GestureDetector element with ID #${elementId} not found.`);
            return;
        }

        this.options = options;

        // --- Gesture State ---
        this.lastTapTime = 0;
        this.tapTimeout = null;
        this.longPressTimeout = null;
        this.isPanning = false;
        this.panStartPoint = { x: 0, y: 0 };
        this.panThreshold = 5; // Pixels to move before a pan is detected

        // --- Bind Handlers ---
        this.handlePointerDown = this.handlePointerDown.bind(this);
        this.handlePointerMove = this.handlePointerMove.bind(this);
        this.handlePointerUp = this.handlePointerUp.bind(this);
        this.fireTap = this.fireTap.bind(this);
        this.fireLongPress = this.fireLongPress.bind(this);

        // Attach the entry-point event listener
        this.element.addEventListener('pointerdown', this.handlePointerDown);
    }

    
    handlePointerDown(event) {
        // Only respond to the primary button (e.g., left mouse click)
        if (event.button !== 0) return;

        const currentTime = Date.now();

        // --- Double Tap Detection ---
        if (currentTime - this.lastTapTime < 300) { // 300ms window for double tap
            clearTimeout(this.tapTimeout);
            this.tapTimeout = null;
            this.lastTapTime = 0;
            if (this.options.onDoubleTapName) {
                window.pywebview.on_gesture_event(this.options.onDoubleTapName, {});
            }
            return;
        }
        
        this.lastTapTime = currentTime;
        this.panStartPoint = { x: event.clientX, y: event.clientY };

        // --- Long Press Detection ---
        if (this.options.onLongPressName) {
            this.longPressTimeout = setTimeout(() => this.fireLongPress(), 500); // 500ms for long press
        }

        // --- Single Tap Detection (will be fired later if not cancelled) ---
        if (this.options.onTapName) {
            this.tapTimeout = setTimeout(() => this.fireTap(), 300);
        }

        // Listen for move/up on the entire document for robust dragging
        document.addEventListener('pointermove', this.handlePointerMove);
        document.addEventListener('pointerup', this.handlePointerUp);
        document.addEventListener('pointercancel', this.handlePointerUp); // Treat cancel like up
    }

    handlePointerMove(event) {
        if (this.isPanning) {
            // --- Continue Panning ---
            const dx = event.clientX - this.panStartPoint.x;
            const dy = event.clientY - this.panStartPoint.y;
            if (this.options.onPanUpdateName) {
                window.pywebview.on_gesture_event(this.options.onPanUpdateName, { dx, dy });
            }
        } else {
            // --- Check if a Pan has Started ---
            const dx = event.clientX - this.panStartPoint.x;
            const dy = event.clientY - this.panStartPoint.y;
            if (Math.sqrt(dx * dx + dy * dy) > this.panThreshold) {
                this.isPanning = true;
                // A pan gesture cancels tap and long press
                clearTimeout(this.tapTimeout);
                this.tapTimeout = null;
                clearTimeout(this.longPressTimeout);
                this.longPressTimeout = null;
                
                if (this.options.onPanStartName) {
                    window.pywebview.on_gesture_event(this.options.onPanStartName, {});
                }
            }
        }
    }

    handlePointerUp(event) {
        // Clean up document-level listeners immediately
        document.removeEventListener('pointermove', this.handlePointerMove);
        document.removeEventListener('pointerup', this.handlePointerUp);
        document.removeEventListener('pointercancel', this.handlePointerUp);

        // Always clear a pending long press if pointer is lifted
        clearTimeout(this.longPressTimeout);
        this.longPressTimeout = null;
        
        if (this.isPanning) {
            // --- End Panning ---
            this.isPanning = false;
            if (this.options.onPanEndName) {
                window.pywebview.on_gesture_event(this.options.onPanEndName, );
            }
        }
    }

    fireTap() {
        if (this.tapTimeout) { // Ensure it wasn't cancelled
            this.tapTimeout = null;
            if (this.options.onTapName) {
                window.pywebview.on_gesture_event(this.options.onTapName, {});
            }
        }
    }
    
    fireLongPress() {
        // A long press cancels a single tap
        clearTimeout(this.tapTimeout);
        this.tapTimeout = null;
        this.lastTapTime = 0; // Prevent next tap from being a double tap
        
        if (this.longPressTimeout) {
            this.longPressTimeout = null;
            if (this.options.onLongPressName) {
                window.pywebview.on_gesture_event(this.options.onLongPressName, {});
            }
        }
    }

    destroy() {
        if (!this.element) return;
        this.element.removeEventListener('pointerdown', this.handlePointerDown);
        this.handlePointerUp(); // Ensure document listeners are cleaned up
        clearTimeout(this.tapTimeout);
        clearTimeout(this.longPressTimeout);
    }
}