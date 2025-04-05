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

function toggleDrawer(side) {
    {
        // Find elements *inside* the function
        const leftDrawer = document.getElementById('leftDrawer');
        const rightDrawer = document.getElementById('rightDrawer');
        const bottomNav = document.getElementById('bottomNav'); // Expects ID to exist

        // Check if drawers exist
        if (!leftDrawer || !rightDrawer) {
            {
                console.error("toggleDrawer: Cannot find left or right drawer element!");
                return;
            }
        }

        const drawer = side === 'left' ? leftDrawer : rightDrawer;
        const isOpen = drawer.classList.contains('open');

        console.log(`Toggling drawer: ${side}, Currently Open: ${isOpen}`); // Debug

        if (isOpen) {
            {
                drawer.classList.remove('open');
            }
        } else {
            {
                drawer.classList.add('open');
                if (bottomNav) {
                    {
                        bottomNav.classList.add('hidden');
                    }
                } else {
                    {
                        console.warn("toggleDrawer: bottomNav element not found to hide.");
                    }
                }
            }
        }

        // Call layout update AFTER changing class
        updateLayout();

        // Check final state to decide on bottomNav visibility
        const leftIsOpenAfter = leftDrawer.classList.contains('open');
        const rightIsOpenAfter = rightDrawer.classList.contains('open');

        if (!leftIsOpenAfter && !rightIsOpenAfter) {
            {
                if (bottomNav) {
                    {
                        bottomNav.classList.remove('hidden');
                    }
                }
            }
        }
    }
}


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