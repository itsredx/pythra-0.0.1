// web/main.js

function handleClick(callback_name) {
    if (window.pywebview) {
        window.pywebview.on_pressed_str(callback_name).then(function(response) {
            console.log(response);
        }).catch(function(error) {
            console.error(error);
        });
    } else {
        console.error('pywebview is not defined');
    }
}

function handleClickOnTap(callback_name, ...args) {
    if (window.pywebview) {
        console.log("index", args);
        window.pywebview.on_pressed(callback_name, ...args).then(function(response) {
            console.log(response);
        }).catch(function(error) {
            console.error(error);
        });
    } else {
        console.error('pywebview is not defined');
    }
}

new QWebChannel(qt.webChannelTransport, function(channel) {
    window.pywebview = channel.objects.pywebview;
});


function updateLayout() {
    {
        // Find elements *inside* the function
        const leftDrawer = document.getElementById('leftDrawer');
        const rightDrawer = document.getElementById('rightDrawer');
        const content = document.getElementById('content');
        const appBar = document.querySelector('.app-bar'); // Assuming only one app-bar

        // Basic null checks
        if (!content || !appBar || !leftDrawer || !rightDrawer) {
            {
                console.warn("updateLayout: Could not find all required elements (content, appBar, leftDrawer, rightDrawer).");
                return;
            }
        }

        const leftOpen = leftDrawer.classList.contains('open');
        const rightOpen = rightDrawer.classList.contains('open');

        // Get widths dynamically from the elements themselves
        const leftDrawerWidth = leftDrawer.offsetWidth;
        const rightDrawerWidth = rightDrawer.offsetWidth;
        console.log(`${leftDrawerWidth}`);

        // Apply styles
        content.style.marginLeft = leftOpen ? `${leftDrawerWidth}px` : '0px';
        content.style.marginRight = rightOpen ? `${rightDrawerWidth}px` : '0px';
        appBar.style.marginLeft = leftOpen ? `${leftDrawerWidth}px` : '0px';
        appBar.style.marginRight = rightOpen ? `${rightDrawerWidth}px` : '0px';

        console.log(`Layout Updated: LeftOpen = ${leftOpen}, RightOpen = ${rightOpen}, LeftWidth = ${leftDrawerWidth}, RightWidth = ${rightDrawerWidth}`); // Debug
    }
}

function findScaffoldContainer(elementId) {
    // Helper to find the main scaffold container element, maybe by ID or class
    // The reconciler should assign the ID based on the Scaffold widget's unique ID.
    // Example: Assume the reconciler uses the widget's unique ID directly.
    // Let's find it by class name for now if ID isn't predictable.
    // This needs coordination with how the reconciler assigns IDs/classes.
    const scaffoldClass = "shared-scaffold"; // Base class prefix
    let currentElement = document.getElementById(elementId);
    while (currentElement && !currentElement.className.startsWith(scaffoldClass)) {
        currentElement = currentElement.parentElement;
        if (currentElement === document.body) return document.querySelector('[class^="shared-scaffold-"]'); // Fallback search
    }
    return currentElement || document.querySelector('[class^="shared-scaffold-"]'); // Fallback search
}

function toggleDrawer(side) {
    // Find the scaffold container - NEEDS to be reliable
    const scaffoldElement = document.querySelector('[class^="shared-scaffold-"]'); // Find by class prefix
    if (!scaffoldElement) {
        console.error("Scaffold container not found for toggleDrawer!");
        return;
    }

    const drawerClass = side === 'left' ? '.scaffold-drawer-left' : '.scaffold-drawer-right';
    const scrimClass = '.scaffold-scrim';

    const drawer = scaffoldElement.querySelector(drawerClass);
    const scrim = scaffoldElement.querySelector(scrimClass);

    if (!drawer) {
        console.error(`Drawer element (${drawerClass}) not found!`);
        return;
    }
    if (!scrim) {
        console.warn(`Scrim element (${scrimClass}) not found. Drawer might work without scrim.`);
    }

    const isOpen = drawer.classList.contains('open');

    console.log(`Toggling drawer: ${side}, Currently Open: ${isOpen}`);

    if (isOpen) {
        drawer.classList.remove('open');
        if (scrim) scrim.classList.remove('active');
    } else {
        drawer.classList.add('open');
        if (scrim) scrim.classList.add('active');
        // Optional: Add click listener to scrim to close drawer
        if (scrim && !scrim.dataset.listenerAttached) {
            scrim.addEventListener('click', () => toggleDrawer(side), {
                once: true
            }); // Close on click, once
            scrim.dataset.listenerAttached = 'true'; // Prevent multiple listeners
        }
    }
    // No layout update needed for overlay drawers
}

// In main JS file or loaded via script tag
function handleItemTap(callbackName, index) {
    console.log(`Item tapped: Index=${index}, Callback=${callbackName}`);
    if (window.pywebview && callbackName) {
        // Assuming the callback registered via Api takes the index as an argument
        // You might need a different pywebview method if args vary
        window.pywebview.on_pressed(callbackName, index, function(result) { // Use on_pressed if passing index
            console.log(`Callback '${callbackName}' result:`, result);
        });
    } else {
        console.error("pywebview not ready or callbackName missing for item tap.");
    }
}


/**
 * Toggles the visibility of a bottom sheet and its associated modal scrim.
 *
 * @param {string} bottomSheetId - The HTML ID of the bottom sheet container element.
 * @param {boolean} show - True to show the bottom sheet, false to hide it.
 * @param {boolean} [isModal=true] - Optional: Whether the bottom sheet is modal (dims background). Defaults to true.
 * @param {string} [scrimClass='scaffold-scrim'] - Optional: The CSS class used to find the scrim element within the scaffold.
 * @param {string} [onDismissedName=''] - Optional: The name of the Python callback (registered via pywebview) to call when dismissed via scrim click.
 */
function toggleBottomSheet(bottomSheetId, show, isModal = true, scrimClass = 'scaffold-scrim', onDismissedName = '') {
    console.log(`toggleBottomSheet called: id=${bottomSheetId}, show=${show}, modal=${isModal}`);

    const bottomSheetElement = document.getElementById(bottomSheetId);
    let scrimElement = null;

    if (!bottomSheetElement) {
        console.error(`BottomSheet element with ID "${bottomSheetId}" not found.`);
        return;
    }

    // Find the scrim relative to the bottom sheet or scaffold if modal
    if (isModal) {
        // Assume scrim is a direct child of the main scaffold container,
        // or search globally if needed. Searching within parent is safer.
        const scaffoldContainer = bottomSheetElement.closest('[class^="shared-scaffold-"]'); // Find nearest scaffold parent
        if (scaffoldContainer) {
            scrimElement = scaffoldContainer.querySelector(`.${scrimClass}`);
        } else {
            // Fallback: search globally (less reliable)
            scrimElement = document.querySelector(`.${scrimClass}`);
            console.warn("Could not find scaffold container, searching globally for scrim.");
        }

        if (!scrimElement) {
            console.warn(`Modal Scrim element with class "${scrimClass}" not found. Bottom sheet will show/hide without scrim.`);
        }
    }

    if (show) {
        // SHOWING the bottom sheet
        bottomSheetElement.classList.add('open');
        bottomSheetElement.setAttribute('aria-hidden', 'false');

        if (scrimElement) {
            scrimElement.classList.add('active');
            scrimElement.setAttribute('aria-hidden', 'false');

            // Add click listener to scrim for dismissal (if not already added)
            // Use a flag to prevent adding multiple listeners if toggle is called rapidly
            if (!scrimElement.dataset.dismissListenerAttached) {
                const dismissHandler = () => {
                    console.log("Scrim clicked, dismissing bottom sheet.");
                    // Hide the sheet first
                    toggleBottomSheet(bottomSheetId, false, isModal, scrimClass, onDismissedName);
                    // Call Python callback if provided
                    if (window.pywebview && onDismissedName) {
                        console.log(`Calling Python dismiss callback: ${onDismissedName}`);
                        window.pywebview.on_pressed_str(onDismissedName, (result) => { // Use on_pressed_str if no args needed
                            console.log(`Dismiss callback '${onDismissedName}' result:`, result);
                        });
                    }
                    // Remove the flag after dismissal
                    delete scrimElement.dataset.dismissListenerAttached;
                };
                // Add listener, only trigger once per attachment
                scrimElement.addEventListener('click', dismissHandler, {
                    once: true
                });
                scrimElement.dataset.dismissListenerAttached = 'true'; // Set flag
                console.log("Added dismiss listener to scrim.");
            }
        }
    } else {
        // HIDING the bottom sheet
        bottomSheetElement.classList.remove('open');
        bottomSheetElement.setAttribute('aria-hidden', 'true');

        if (scrimElement) {
            scrimElement.classList.remove('active');
            scrimElement.setAttribute('aria-hidden', 'true');
            // Remove dismiss listener flag - the listener itself is removed by {once: true}
            delete scrimElement.dataset.dismissListenerAttached;
            console.log("Removed dismiss listener flag from scrim.");
        }
    }
}

/**
 * Toggles the visibility of a SnackBar element using CSS transitions.
 *
 * @param {string} snackBarId - The HTML ID of the SnackBar container element.
 * @param {boolean} show - True to show (slide up), false to hide (slide down).
 */
function toggleSnackBar(snackBarId, show) {
    console.log(`toggleSnackBar called: id=${snackBarId}, show=${show}`);

    const snackBarElement = document.getElementById(snackBarId);

    if (!snackBarElement) {
        console.error(`SnackBar element with ID "${snackBarId}" not found.`);
        return;
    }

    // Use a separate 'visible' class to handle initial state and prevent animation on load if needed
    // Or rely purely on 'open' class for transition

    if (show) {
        // Ensure it's visually ready before animating (though CSS handles transform start)
        snackBarElement.style.display = 'flex'; // Make sure it's flex if previously 'none'

        // Add small delay before adding 'open' to ensure transition runs correctly? Sometimes needed.
        requestAnimationFrame(() => { // Use rAF for smoother timing
            requestAnimationFrame(() => {
                snackBarElement.classList.add('open');
                snackBarElement.setAttribute('aria-hidden', 'false');
                console.log(`SnackBar ${snackBarId} class added: open`);
            });
        });


    } else {
        // HIDING the snack bar
        snackBarElement.classList.remove('open');
        snackBarElement.setAttribute('aria-hidden', 'true');
        console.log(`SnackBar ${snackBarId} class removed: open`);

        // Optional: Set display to 'none' after transition completes to remove from layout
        // Only do this if pointer-events: none isn't sufficient
        // snackBarElement.addEventListener('transitionend', () => {
        //     if (!snackBarElement.classList.contains('open')) { // Check state again in case it reopened
        //         snackBarElement.style.display = 'none';
        //     }
        // }, { once: true });
    }
}



/**
 * Toggles the visibility of an in-page Dialog element and its modal scrim.
 *
 * @param {string} dialogId - The HTML ID of the Dialog container element.
 * @param {boolean} show - True to show the dialog, false to hide it.
 * @param {boolean} [isModal=true] - Optional: Whether the dialog is modal. Defaults to true.
 * @param {string} [scrimClass='dialog-scrim'] - Optional: The CSS class for the scrim element.
 * @param {string} [onDismissedName=''] - Optional: Python callback name for scrim click dismissal.
 */
function toggleDialog(dialogId, show, isModal = true, scrimClass = 'dialog-scrim', onDismissedName = '') {
    console.log(`toggleDialog called: id=${dialogId}, show=${show}, modal=${isModal}`);

    const dialogElement = document.getElementById(dialogId);
    // Scrim is usually created/managed globally or within the main body by the framework
    let scrimElement = document.querySelector(`.${scrimClass}`);

    if (!dialogElement) {
        console.error(`Dialog element with ID "${dialogId}" not found.`);
        return;
    }

    // Ensure scrim exists if modal, create if necessary (basic version)
    // A more robust framework might always ensure the scrim div exists in the initial HTML.
    if (isModal && !scrimElement) {
        console.warn(`Scrim element with class "${scrimClass}" not found. Creating one.`);
        scrimElement = document.createElement('div');
        scrimElement.className = scrimClass;
        scrimElement.setAttribute('aria-hidden', 'true');
        document.body.appendChild(scrimElement); // Append to body
    } else if (!isModal && scrimElement) {
        // If dialog is NOT modal, ensure any existing scrim is hidden
        scrimElement.classList.remove('active');
        scrimElement.setAttribute('aria-hidden', 'true');
        delete scrimElement.dataset.dismissListenerAttached; // Clean up listener flag
    }


    if (show) {
        // SHOWING the dialog
        // Ensure display is block/flex before adding open class for transition
        // (CSS for .shared-dialog-* should set display: flex)
        // dialogElement.style.display = 'flex'; // Or 'block' based on your CSS

        // Use rAF for smoother transition start
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                dialogElement.classList.add('open');
                dialogElement.setAttribute('aria-hidden', 'false');
                console.log(`Dialog ${dialogId} class added: open`);
            });
        });


        if (scrimElement && isModal) {
            scrimElement.classList.add('active');
            scrimElement.setAttribute('aria-hidden', 'false');

            // Add scrim click listener for dismissal
            if (!scrimElement.dataset.dismissListenerAttached) {
                const dismissHandler = () => {
                    console.log("Dialog scrim clicked, dismissing dialog.");
                    // Hide the dialog first
                    toggleDialog(dialogId, false, isModal, scrimClass, onDismissedName);
                    // Call Python callback if provided
                    if (window.pywebview && onDismissedName) {
                        console.log(`Calling Python dismiss callback: ${onDismissedName}`);
                        window.pywebview.on_pressed_str(onDismissedName, (result) => {
                            console.log(`Dismiss callback '${onDismissedName}' result:`, result);
                        });
                    }
                    // Clean up flag
                    delete scrimElement.dataset.dismissListenerAttached;
                };
                scrimElement.addEventListener('click', dismissHandler, {
                    once: true
                });
                scrimElement.dataset.dismissListenerAttached = 'true';
                console.log("Added dismiss listener to dialog scrim.");
            }
        }
    } else {
        // HIDING the dialog
        dialogElement.classList.remove('open');
        dialogElement.setAttribute('aria-hidden', 'true');
        console.log(`Dialog ${dialogId} class removed: open`);

        if (scrimElement && isModal) {
            scrimElement.classList.remove('active');
            scrimElement.setAttribute('aria-hidden', 'true');
            delete scrimElement.dataset.dismissListenerAttached; // Clean up flag
            console.log("Removed dismiss listener flag from dialog scrim.");
        }

        // Optional: Set display to 'none' after transition completes.
        // dialogElement.addEventListener('transitionend', () => {
        //     if (!dialogElement.classList.contains('open')) {
        //         dialogElement.style.display = 'none';
        //     }
        // }, { once: true });
    }
}

// --- Includes other necessary JS functions ---
// QWebChannel setup, handleClick, handleItemTap, toggleDrawer, toggleBottomSheet...
// ...


/*
function handleClick(callback_name) {
    if (window.pywebview) {
        window.pywebview.api.on_pressed(callback_name).then(function(response) {
            console.log(response);
        }).catch(function(error) {
            console.error(error);
        });
    } else {
        console.error('pywebview is not defined');
    }
}


function openDrawer() {
    var drawer = document.getElementById('drawer');
    drawer.classList.remove('drawer-closed');
    drawer.classList.add('drawer-open');
}

function closeDrawer() {
    var drawer = document.getElementById('drawer');
    drawer.classList.remove('drawer-open');
    drawer.classList.add('drawer-closed');
}

*/