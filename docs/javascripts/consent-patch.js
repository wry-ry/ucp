/*
 * UCP Consent Patch:
 * Syncs consent across versions by copying LocalStorage keys.
 * Includes Debug Logging.
 */
(function() {
  var suffix = ".__consent";

  function syncConsent() {
    try {
      console.log("[UCP Sync] Scanning LocalStorage...");
      var foundVal = null;
      var foundKey = null;

      // 1. Search for existing consent
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k.endsWith(suffix)) {
          var v = localStorage.getItem(k);
          if (v && v.indexOf("{") !== -1) {
            foundVal = v;
            foundKey = k;
            break;
          }
        }
      }

      if (foundVal) {
        console.log("[UCP Sync] Found consent in:", foundKey);
        
        // Root Key
        if (localStorage.getItem("/.__consent") !== foundVal) {
          localStorage.setItem("/.__consent", foundVal);
          console.log("[UCP Sync] Synced to Root: /.__consent");
        }

        // Current Path Key
        var path = window.location.pathname.replace(/index\.html$/, "");
        if (!path.endsWith("/")) path += "/";
        var currentKey = (path === "/") ? "/.__consent" : path + "." + "__consent";

        if (localStorage.getItem(currentKey) !== foundVal) {
          localStorage.setItem(currentKey, foundVal);
          console.log("[UCP Sync] Synced to Current:", currentKey);
        }
      } else {
          console.log("[UCP Sync] No consent found.");
      }
    } catch (e) {
      console.warn("[UCP Sync] Error:", e);
    }
  }

  // Run on load
  syncConsent();

  // Run on click
  document.addEventListener('click', function(e) {
    if (e.target.closest('.md-consent__action')) {
      console.log("[UCP Sync] Action clicked. Syncing soon...");
      setTimeout(syncConsent, 500);
    }
  });
})();
