/**
 * dropdown.js
 * Handles the cascading updates: Symbol -> Expiry -> Strikes
 */

const EMPTY_OPTION = '<option value="">-- Select --</option>';

function clearExpiryAndStrikes() {
    document.getElementById("expiry-select").innerHTML = EMPTY_OPTION;
    const ceSelects = ["main-call-base", "ltp-call-base"];
    const peSelects = ["main-put-base", "ltp-put-base"];
    ceSelects.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = EMPTY_OPTION;
    });
    peSelects.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = EMPTY_OPTION;
    });
}

function clearStrikes() {
    const ceSelects = ["main-call-base", "ltp-call-base"];
    const peSelects = ["main-put-base", "ltp-put-base"];
    ceSelects.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = EMPTY_OPTION;
    });
    peSelects.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = EMPTY_OPTION;
    });
}

async function updateExpiryDropdown() {
    const symbol = document.getElementById("symbol-select").value;
    const expirySelect = document.getElementById("expiry-select");

    // Clear expiry and strikes when symbol changes
    clearExpiryAndStrikes();

    try {
        const response = await fetch(`/get-expiries/${encodeURIComponent(symbol)}`);
        const expiries = await response.json();

        // 1. Populate the Expiry dropdown with empty first
        expirySelect.innerHTML = EMPTY_OPTION + expiries.map(
            (e) => `<option value="${e}">${e}</option>`
        ).join("");

        // 2. Trigger the Strike update when user selects expiry (not auto anymore)
    } catch (error) {
        console.error("Error fetching expiries:", error);
    }
}

async function updateStrikeDropdowns() {
    const symbol = document.getElementById("symbol-select").value;
    const expiry = document.getElementById("expiry-select").value;

    // Clear strikes when expiry changes
    clearStrikes();

    // Safety check: Don't fetch if expiry isn't selected yet
    if (!expiry) return;

    try {
        const response = await fetch(
            `/get-strikes/${encodeURIComponent(symbol)}/${encodeURIComponent(expiry)}`
        );
        const data = await response.json(); // Expected: { CE: [...], PE: [...] }

        const ceSelects = ["main-call-base", "ltp-call-base"];
        const peSelects = ["main-put-base", "ltp-put-base"];

        // Populate CE dropdowns with empty first
        ceSelects.forEach((id) => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = EMPTY_OPTION + data.CE.map(
                    (s) => `<option value="${s}">${s}</option>`
                ).join("");
            }
        });

        // Populate PE dropdowns with empty first
        peSelects.forEach((id) => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = EMPTY_OPTION + data.PE.map(
                    (s) => `<option value="${s}">${s}</option>`
                ).join("");
            }
        });

        console.log(`Strikes updated for ${symbol} - ${expiry}`);
    } catch (error) {
        console.error("Failed to update strikes:", error);
    }
}

// Initialize the chain on page load
document.addEventListener("DOMContentLoaded", () => {
    // Initialize with empty options
    clearExpiryAndStrikes();
    updateExpiryDropdown();
});
