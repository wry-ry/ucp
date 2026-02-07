/*
 * Sync consent across versions by copying LocalStorage keys.
 * Material Theme namespaces LS keys by path (e.g. "/.__consent", "/latest/.__consent").
 * This script finds any existing consent and copies it to the current path's key.
 * If sync is successful, it hides the banner immediately.
 */
(function() {
  var suffix = ".__consent";
  
  function syncConsent() {
    try {
      var foundValue = null;
      
      // 1. Find ANY existing consent in LS
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k.endsWith(suffix)) {
           var val = localStorage.getItem(k);
           if (val && val.indexOf("analytics") !== -1) { 
               foundValue = val;
               break; 
           }
        }
      }
      
      if (foundValue) {
          var path = window.location.pathname;
          path = path.replace(/index\.html$/, "");
          if (!path.endsWith("/")) path += "/";
          
          var currentKey = path + "." + "__consent";
          var rootKey = "/.__consent";
          
          // 3. Sync to Root
          if (localStorage.getItem(rootKey) !== foundValue) {
              localStorage.setItem(rootKey, foundValue);
          }
          
          // 4. Sync to Current Path & Hide Banner
          // Even if key existed (but was different? unlikely), we ensure it matches.
          // If we found ANY consent, we assume user has consented.
          
          // We check if the banner is visible (implied by 'hidden' attribute missing or false)
          var banner = document.querySelector('[data-md-component="consent"]');
          
          // Determine if we need to apply it
          if (localStorage.getItem(currentKey) !== foundValue) {
              localStorage.setItem(currentKey, foundValue);
          }
          
          // If we have consent (foundValue), forcefully hide the banner
          // because the theme script ran BEFORE us and might have shown it.
          if (banner && !banner.hidden) {
              banner.hidden = true;
              // console.log("Hiding consent banner (synced).");
          }
      }
    } catch (e) {
      console.warn("[UCP Sync] Error:", e);
    }
  }

  // Run immediately
  syncConsent();
  
  // Run on click
  document.addEventListener('click', function(e) {
    if (e.target.closest('.md-consent__action')) {
      setTimeout(syncConsent, 500);
    }
  });
})();
