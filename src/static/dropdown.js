// Function to update the strike dropdowns based on symbol
async function updateStrikeDropdowns() {
    const symbol = document.getElementById("symbol-select").value;

    // needed by your Python function (e.g., "BANKNIFTY (2026-02-24)")
    try {
        const response = await fetch(
            `/get-strikes/${encodeURIComponent(symbol)}`,
        );
        const data = await response.json(); // Expected: { CE: [...], PE: [...] }

        // List of all strike select IDs in your index.html
        const ceSelects = ["main-call-base", "hedge-call-base"];
        const peSelects = ["main-put-base", "hedge-put-base"];

        // Populate CE dropdowns
        ceSelects.forEach((id) => {
            const select = document.getElementById(id);
            select.innerHTML = data.CE.map(
                (s) => `<option value="${s}">${s}</option>`,
            ).join("");
        });

        // Populate PE dropdowns
        peSelects.forEach((id) => {
            const select = document.getElementById(id);
            select.innerHTML = data.PE.map(
                (s) => `<option value="${s}">${s}</option>`,
            ).join("");
        });

        console.log(`Dropdowns updated for ${symbol}`);
    } catch (error) {
        console.error("Failed to update dependent dropdowns:", error);
    }
}

// Attach the listener
document
    .getElementById("symbol-select")
    .addEventListener("change", updateStrikeDropdowns);

// Run once on load to populate initial values
document.addEventListener("DOMContentLoaded", updateStrikeDropdowns);
