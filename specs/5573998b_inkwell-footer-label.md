# Plan for Baseline proof footer label in Inkwell

## Summary
Add "Baseline proof" as a small footer label to the Inkwell blog app, likely in the sidebar footer that currently shows post and word counts.

## Changes Required

1. **Edit `/home/exedev/app/apps/inkwell/public/index.html`**
   - Locate the sidebar footer element (line 68-70)
   - Add a new span element with class for styling that displays "Baseline proof"
   - Keep it small and minimally styled

2. **Optional: Add CSS styling for the new footer label**
   - If needed, add minimal CSS in `/home/exedev/app/apps/inkwell/public/style.css`
   - Should be small, perhaps with subtle styling

## Files to modify
- `apps/inkwell/public/index.html` - primary change
- `apps/inkwell/public/style.css` - optional styling (check if needed first)

## Verification
- Start the Inkwell app: `bun run apps/inkwell/server.ts`
- Open in browser and verify "Baseline proof" appears in the footer
- Check that the change is minimal and doesn't break existing functionality
- Run existing tests: `bun test apps/inkwell/server.test.ts`