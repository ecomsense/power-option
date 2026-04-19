/**
 * toggle.js
 * Manages UI modes (Buy/Sell) and button states
 */

// Global state to track if we are in Buy or Sell mode for each table
window.tableModes = {
    main: 'BUY',
    ltp: 'BUY'
};

/**
 * Toggles the button state between Buy and Sell
 * Handles visual classes and internal state.
 */
function toggleSide(type) {
    const checkboxId = type === 'main' ? 'main-side-toggle' : 'ltp-side-toggle';
    const checkbox = document.getElementById(checkboxId);
    
    if (!checkbox) {
        console.log(`toggleSide: checkbox not found for ${type}`);
        return;
    }
    
    const isChecked = checkbox.checked;
    
    // Toggle behavior: unchecked=BUY, checked=SELL
    if (isChecked) {
        window.tableModes[type] = 'SELL';
    } else {
        window.tableModes[type] = 'BUY';
    }
    
    console.log(`toggleSide: ${type} checkbox.checked=${isChecked}, mode=${window.tableModes[type]}`);
}

// Optional: Global helper to check mode from other scripts
function getTableMode(type) {
    return window.tableModes[type] || 'BUY';
}
