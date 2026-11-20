/*
 * Optimizer Step — site settings. Edit this file, then run `python scripts/build_pages.py`.
 *
 * enrollmentEndpoint  The Google Apps Script web app URL (ends in /exec). Signups and the
 *                     live seat count come from here. See backend/apps-script/README.md.
 * capacity            Founding seats shown before the live count loads. The real number
 *                     comes from the Settings sheet in the signups spreadsheet.
 * showCountsAfter     Hide the "N of 100 left" bar until this many seats are claimed, so a
 *                     fresh campaign shows "100 free founding seats" instead of "100 of 100 left".
 *
 * Tracking IDs: paste an ID and that tool loads on every page. Leave empty to keep it off.
 *   ga4MeasurementId    "G-XXXXXXXXXX"  (Google Analytics 4)
 *   metaPixelId         "123456789012345" (Meta / Instagram / Facebook ads)
 *   googleAdsId         "AW-123456789"  (Google / YouTube ads)
 *   googleAdsLeadLabel  conversion label for sign-ups, e.g. "AbC-D_efG-h12_34-567"
 *   clarityProjectId    "abcdefghij"    (Microsoft Clarity heatmaps and recordings)
 */
window.OS_CONFIG = {
  enrollmentEndpoint: "https://script.google.com/macros/s/AKfycbwIJKFScnpdf3f6hOsWhtm7kzTjuc5_8yj7oHDtSJPnXf7vkKjtG61HE3I_s4SQFKFX/exec",
  capacity: 100,
  showCountsAfter: 10,
  plannedPriceINR: 4999,
  statsRefreshSeconds: 90,
  tracking: {
    ga4MeasurementId: "",
    metaPixelId: "",
    googleAdsId: "",
    googleAdsLeadLabel: "",
    clarityProjectId: ""
  }
};
