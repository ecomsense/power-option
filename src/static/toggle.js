/**
 * toggle.js
 * Manages UI modes (Buy/Sell) and button states
 */

// Global state to track if we are in Buy or Sell mode for each table
const tableModes = {
    diff: 'BUY',
    hedge: 'BUY'
};

/**
 * Toggles the button state between Buy and Sell
 * Handles visual classes and internal state.
 */
function toggleSide(type) {
    const checkboxId = type === 'diff' ? 'main-side-toggle' : 'hedge-side-toggle';
    const checkbox = document.getElementById(checkboxId);
    
    if (!checkbox) return;
    
    const isChecked = checkbox.checked;
    
    if (isChecked) {
        tableModes[type] = 'SELL';
    } else {
        tableModes[type] = 'BUY';
    }
    
    console.log(`${type} table updated to: ${tableModes[type]}`);
}

// Optional: Global helper to check mode from other scripts
function getTableMode(type) {
    return tableModes[type] || 'BUY';
}
