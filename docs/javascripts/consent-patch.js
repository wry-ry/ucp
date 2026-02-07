/*
 * Force consent cookie to have path=/ to share between versions.
 * Event-driven: checks on load and when the user clicks a consent button.
 */
(function() {
  var name = 'mkdocs-consent';

  function patchCookie() {
    try {
      if (document.cookie.indexOf(name + '=') !== -1) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length >= 2) {
          var val = parts.pop().split(";").shift();
          // Re-set with path=/
          var d = new Date();
          d.setTime(d.getTime() + (365*24*60*60*1000));
          var expires = "expires="+ d.toUTCString();
          document.cookie = name + "=" + val + ";" + expires + ";path=/;SameSite=Lax";
        }
      }
    } catch (e) {
      console.warn("Unable to patch consent cookie path", e);
    }
  }

  // 1. Run immediately on load for returning users
  patchCookie();

  // 2. Listen for clicks on the consent banner buttons
  document.addEventListener('click', function(e) {
    // material theme consent buttons usually have this class or similar structure
    if (e.target.closest('.md-consent__action')) {
      // Wait a brief moment for the theme's default handler to set the initial cookie
      setTimeout(patchCookie, 200);
    }
  });
})();
