/*
 * Force consent cookie to have path=/ to share between versions.
 */
(function() {
  var name = 'mkdocs-consent';

  function patchCookie() {
    try {
      console.log("[UCP Consent] Checking for cookie...");
      if (document.cookie.indexOf(name + '=') !== -1) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length >= 2) {
          var val = parts.pop().split(";").shift();
          console.log("[UCP Consent] Found cookie value:", val);
          
          // Re-set with path=/
          var d = new Date();
          d.setTime(d.getTime() + (365*24*60*60*1000));
          var expires = "expires="+ d.toUTCString();
          document.cookie = name + "=" + val + ";" + expires + ";path=/;SameSite=Lax";
          console.log("[UCP Consent] Patched cookie to root path.");
        }
      } else {
          console.log("[UCP Consent] Cookie not found.");
      }
    } catch (e) {
      console.warn("[UCP Consent] Error:", e);
    }
  }

  // Run on load
  patchCookie();

  // Run on click
  document.addEventListener('click', function(e) {
    if (e.target.closest('.md-consent__action')) {
      console.log("[UCP Consent] User clicked action. Patching soon...");
      setTimeout(patchCookie, 200);
    }
  });
})();
