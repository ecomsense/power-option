# Power Option - UI Improvements Plan
## Priority Items (Items 2, 3, 5, 7, 9)
### Item 2: Add sub-labels for controls
- **Location**: Both Main and Hedge tables
- **Layout**: Separate label row above control row
- **Labels**:
  - Main Table: Symbol, Expiry, Call, Put, Strikes, Qty, **Actions**
  - Hedge Table: Call, Put, Strikes, Qty, **Actions**
### Item 3: Add 'Lots' label to hedge table
- Rename "Lots" to "Qty" everywhere
- Add `<label for="hedge-qty">Qty</label>` before hedge quantity input
### Item 5: WebSocket connection status indicator
- Add status dot in control bar
- Green = connected, Red = disconnected
- Updates on WebSocket open/close events in dashboard.js
### Item 7: Row hover effect
- Add CSS: `tr:hover { background: #333; }` for table rows
- Improves readability when tracking across columns
### Item 9: Fire vs Square mode indicator
- Add badge showing "FIRE MODE" (purple) or "SQUARE MODE" (orange)
- Place in top control bar of each table
- Color matches Fire (violet) and Square (orange) buttons
