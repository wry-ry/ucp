/*
 * UCP Consent Patch:
 * 1. Scans LocalStorage for ANY consent key (ending in .__consent).
 * 2. If found, ensures the Root Key (/.__consent) and Current Key match it.
 * 3. Hides the consent banner if any consent is present.
 */
(function() {
  console.log("[UCP Patch] Starting...");
  var suffix = ".__consent";
  var foundVal = null;
  var foundKey = null;

  // 1. Search for existing consent
  for (var i = 0; i < localStorage.length; i++) {
    var k = localStorage.key(i);
    if (k.endsWith(suffix)) {
      var v = localStorage.getItem(k);
      // Valid consent usually looks like {"analytics":...}
      if (v && v.indexOf("{") !== -1) {
        foundVal = v;
        foundKey = k;
        console.log("[UCP Patch] Found existing consent in:", k, v);
        break;
      }
    }
  }

  // 2. Sync and Hide
  if (foundVal) {
    // Sync to Root (Master Key)
    var rootKey = "/.__consent";
    if (localStorage.getItem(rootKey) !== foundVal) {
      localStorage.setItem(rootKey, foundVal);
      console.log("[UCP Patch] Synced to Root:", rootKey);
    }

    // Sync to Current Path (Active Key)
    // We construct the key the same way the theme likely does
    var path = window.location.pathname.replace(/index\.html$/, "");
    if (!path.endsWith("/")) path += "/";
    var currentKey = path + "." + "__consent";
    
    // Fix for root path case (avoid /..__consent if logic differs)
    if (path === "/") currentKey = "/.__consent";

    if (localStorage.getItem(currentKey) !== foundVal) {
      localStorage.setItem(currentKey, foundVal);
      console.log("[UCP Patch] Synced to Current:", currentKey);
    }

    // 3. Force Hide Banner
    var banner = document.querySelector('[data-md-component="consent"]');
    if (banner) {
      banner.hidden = true;
      banner.style.display = 'none'; // Force hide via CSS
      console.log("[UCP Patch] Banner hidden forcibly.");
    } else {
      console.log("[UCP Patch] Banner element not found in DOM.");
    }
  } else {
    console.log("[UCP Patch] No existing consent found.");
  }
})();
