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
 * Toggles the button state between Buy (B) and Sell (S)
 * Handles visual classes and internal state.
 */
function toggleSide(type) {
    // Map the logic type to the specific HTML ID
    const buttonId = type === 'diff' ? 'main-side-toggle' : 'hedge-side-toggle';
    const btn = document.getElementById(buttonId);
    
    if (!btn) return;

    const isBuy = tableModes[type] === 'BUY';
    
    if (isBuy) {
        // Switch to SELL
        tableModes[type] = 'SELL';
        btn.innerText = 'S';
        btn.classList.remove('buy-mode');
        btn.classList.add('sell-mode');
    } else {
        // Switch to BUY
        tableModes[type] = 'BUY';
        btn.innerText = 'B';
        btn.classList.remove('sell-mode');
        btn.classList.add('buy-mode');
    }
    
    console.log(`${type} table updated to: ${tableModes[type]}`);
}

// Optional: Global helper to check mode from other scripts
function getTableMode(type) {
    return tableModes[type] || 'BUY';
}
