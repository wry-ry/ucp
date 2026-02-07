/*
 * Force consent cookie to have path=/ to share between versions.
 * This ensures that accepting cookies on a versioned subpath (e.g. /latest/)
 * applies to the entire domain.
 *
 * This script polls periodically to catch the moment the user clicks "Accept".
 */
(function() {
  var name = 'mkdocs-consent';
  
  function patchCookie() {
    try {
      if (document.cookie.indexOf(name + '=') !== -1) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length === 2) {
          var val = parts.pop().split(";").shift();
          
          // Re-set it with path=/
          var d = new Date();
          d.setTime(d.getTime() + (365*24*60*60*1000)); // 1 year
          var expires = "expires="+ d.toUTCString();
          
          // Write the cookie to the root path
          document.cookie = name + "=" + val + ";" + expires + ";path=/;SameSite=Lax";
          
          // Optional: Clear the specific path cookie to avoid duplication/confusion?
          // document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=" + window.location.pathname;
        }
      }
    } catch (e) {
      console.warn("Unable to patch consent cookie path", e);
    }
  }

  // Check immediately
  patchCookie();
  
  // Check every 1 second to catch user acceptance in real-time
  setInterval(patchCookie, 1000);
  
  console.log("UCP Consent Patch loaded.");
})();
