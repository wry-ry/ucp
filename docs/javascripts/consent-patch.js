/*
 * UCP Consent Patch:
 * Syncs consent across versions by copying LocalStorage keys.
 * This ensures that accepting cookies on a versioned subpath (e.g. /latest/)
 * applies to the entire domain.
 */
(function() {
  var suffix = ".__consent";

  function syncConsent() {
    try {
      var foundVal = null;

      // 1. Search for existing consent
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k.endsWith(suffix)) {
          var v = localStorage.getItem(k);
          if (v && v.indexOf("{") !== -1) {
            foundVal = v;
            break;
          }
        }
      }

      // 2. Sync if found
      if (foundVal) {
        // Root Key
        if (localStorage.getItem("/.__consent") !== foundVal) {
          localStorage.setItem("/.__consent", foundVal);
        }

        // Current Path Key
        var path = window.location.pathname.replace(/index\.html$/, "");
        if (!path.endsWith("/")) path += "/";
        
        var currentKey = (path === "/") ? "/.__consent" : path + "." + "__consent";

        if (localStorage.getItem(currentKey) !== foundVal) {
          localStorage.setItem(currentKey, foundVal);
        }
        
        // Force hide banner if we have consent
        // This handles cases where the theme script ran first and showed the banner
        var banner = document.querySelector('[data-md-component="consent"]');
        if (banner && !banner.hidden) {
            banner.hidden = true;
            // Also force style in case hidden attribute is not enough or overridden
            if (banner.style) banner.style.display = 'none';
        }
      }
    } catch (e) {
      console.warn("Unable to sync consent", e);
    }
  }

  // Run on load
  syncConsent();

  // Run on click
  document.addEventListener('click', function(e) {
    if (e.target.closest('.md-consent__action')) {
      setTimeout(syncConsent, 500);
    }
  });
})();
