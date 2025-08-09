/**
 * PythraDropdown: Client-side engine for a custom Dropdown widget.
 *
 * Handles toggling the dropdown menu, closing it when clicking outside,
 * and sending the selected value back to the Python backend.
 */
export class PythraDropdown {
    constructor(elementId, options) {
        this.container = document.getElementById(elementId);
        if (!this.container) {
            console.error(`Dropdown container with ID #${elementId} not found.`);
            return;
        }

        console.log(`✅ PythraDropdown engine is initializing for #${elementId}`);

        this.options = options;
        this.valueContainer = this.container.querySelector('.dropdown-value-container');
        this.menu = this.container.querySelector('.dropdown-menu');
        this.items = this.menu.querySelectorAll('.dropdown-item');

        // Bind 'this' to maintain context in event handlers
        this.toggleMenu = this.toggleMenu.bind(this);
        this.handleItemClick = this.handleItemClick.bind(this);
        this.handleClickOutside = this.handleClickOutside.bind(this);

        // Attach event listeners
        this.valueContainer.addEventListener('click', this.toggleMenu);
        this.items.forEach(item => {
            item.addEventListener('click', this.handleItemClick);
        });
    }

    toggleMenu(event) {
        event.stopPropagation(); // Prevent click from bubbling to the document
        const isCurrentlyOpen = this.container.classList.toggle('open');
        console.log("Value container Clicked");
        
        if (isCurrentlyOpen) {
            // If we just opened the menu, listen for clicks outside to close it
            document.addEventListener('click', this.handleClickOutside);
        } else {
            // If we just closed it, stop listening
            document.removeEventListener('click', this.handleClickOutside);
        }
    }

    handleItemClick(event) {
        const selectedValue = event.currentTarget.dataset.value;
        const selectedLabel = event.currentTarget.textContent;

        console.log("Dropdown option Clicked");
        
        // 1. Update the display value immediately for instant feedback
        this.valueContainer.querySelector('span').textContent = selectedLabel;
        
        // 2. Send the selected *value* back to the Python backend
        if (window.pywebview && this.options.onChangedName) {
            window.pywebview.on_input_changed(this.options.onChangedName, selectedValue);
        }
        
        // 3. Close the menu
        this.closeMenu();
    }
    
    closeMenu() {
        if (this.container.classList.contains('open')) {
            this.container.classList.remove('open');
            document.removeEventListener('click', this.handleClickOutside);
        }
    }

    handleClickOutside(event) {
        // If the click is outside the main container, close the menu
        if (!this.container.contains(event.target)) {
            this.closeMenu();
        }
    }

    destroy() {
        // Cleanup to prevent memory leaks
        if (!this.container) return;
        this.valueContainer.removeEventListener('click', this.toggleMenu);
        this.items.forEach(item => {
            item.removeEventListener('click', this.handleItemClick);
        });
        document.removeEventListener('click', this.handleClickOutside);
    }
}