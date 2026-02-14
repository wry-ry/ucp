document.addEventListener("DOMContentLoaded", function() {
    var header = document.querySelector(".md-header");
    if (!header) return;

    function moveSelector() {
        // Look for the option containing md-select (but not palette)
        var options = document.querySelectorAll(".md-header__option");
        var versionContainer = null;
        
        options.forEach(function(opt) {
            if (opt.querySelector(".md-select") && !opt.hasAttribute("data-md-component")) {
                versionContainer = opt;
            }
        });

        var searchButton = document.querySelector("label[for='__search']");
        var headerInner = document.querySelector(".md-header__inner");
        
        if (versionContainer && searchButton && headerInner) {
             // Move only if not already before searchButton
             if (versionContainer.nextElementSibling !== searchButton) {
                 headerInner.insertBefore(versionContainer, searchButton);
                 versionContainer.style.marginRight = "8px";
             }
        }
    }

    // Try immediately
    moveSelector();

    // Observe changes in header (e.g. mike injecting the selector)
    var observer = new MutationObserver(moveSelector);
    observer.observe(header, { childList: true, subtree: true });
});
