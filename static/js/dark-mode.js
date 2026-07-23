const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
const currentTheme = localStorage.getItem('theme');

// Function to set Dark Mode
function setDarkMode() {
    document.body.classList.add('dark-mode');
    const navbar = document.querySelector('.main-header.navbar');
    if (navbar) {
        navbar.classList.remove('navbar-white', 'navbar-light');
        navbar.classList.add('navbar-dark');
    }
}

// Function to set Light Mode
function setLightMode() {
    document.body.classList.remove('dark-mode');
    const navbar = document.querySelector('.main-header.navbar');
    if (navbar) {
        navbar.classList.add('navbar-white', 'navbar-light');
        navbar.classList.remove('navbar-dark');
    }
}

// Initialize theme from localStorage
if (currentTheme) {
    if (currentTheme === 'dark') {
        if (toggleSwitch) toggleSwitch.checked = true;
        setDarkMode();
    } else {
        setLightMode();
    }
}

// Handle switch change
if (toggleSwitch) {
    toggleSwitch.addEventListener('change', function(e) {
        if (e.target.checked) {
            setDarkMode();
            localStorage.setItem('theme', 'dark');
        } else {
            setLightMode();
            localStorage.setItem('theme', 'light');
        }    
    }, false);
}
