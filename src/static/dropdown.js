/**
 * dropdown.js
 * Handles the cascading updates: Symbol -> Expiry -> Strikes
 */

async function updateExpiryDropdown() {
    const symbol = document.getElementById("symbol-select").value;
    const expirySelect = document.getElementById("expiry-select");

    try {
        const response = await fetch(`/get-expiries/${encodeURIComponent(symbol)}`);
        const expiries = await response.json();

        // 1. Populate the Expiry dropdown
        expirySelect.innerHTML = expiries.map(
            (e) => `<option value="${e}">${e}</option>`
        ).join("");

        // 2. Trigger the Strike update immediately for the first expiry in the list
        if (expiries.length > 0) {
            updateStrikeDropdowns();
        }
        
    } catch (error) {
        console.error("Error fetching expiries:", error);
    }
}

async function updateStrikeDropdowns() {
    const symbol = document.getElementById("symbol-select").value;
    const expiry = document.getElementById("expiry-select").value;

    // Safety check: Don't fetch if expiry isn't selected yet
    if (!expiry) return;

    try {
        const response = await fetch(
            `/get-strikes/${encodeURIComponent(symbol)}/${encodeURIComponent(expiry)}`
        );
        const data = await response.json(); // Expected: { CE: [...], PE: [...] }

        const ceSelects = ["main-call-base", "hedge-call-base"];
        const peSelects = ["main-put-base", "hedge-put-base"];

        // Populate CE dropdowns
        ceSelects.forEach((id) => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = data.CE.map(
                    (s) => `<option value="${s}">${s}</option>`
                ).join("");
            }
        });

        // Populate PE dropdowns
        peSelects.forEach((id) => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = data.PE.map(
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
    updateExpiryDropdown();
});
