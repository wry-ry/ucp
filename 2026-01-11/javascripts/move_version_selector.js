document.addEventListener("DOMContentLoaded", function() {
    // console.log("Move Version Selector: Loaded");
    var header = document.querySelector(".md-header");
    if (!header) return;

    function moveSelector() {
        // Find .md-select
        var select = header.querySelector(".md-select");
        if (!select) return;

        // Find its container (md-header__option)
        var container = select.closest(".md-header__option");
        
        // If not in an option container, use select itself (though usually it is wrapped)
        var target = container || select;

        // Check if it's the Palette selector
        if (container && container.getAttribute("data-md-component") === "palette") {
            // This is palette, ignore
            // Look for another select?
            // If there are multiple selects, querySelector might return palette first.
            // Let's iterate all selects.
            return;
        }
        
        // Better search: find all selects and pick the one that isn't palette
        var selects = header.querySelectorAll(".md-select");
        target = null;
        for (var i = 0; i < selects.length; i++) {
            var s = selects[i];
            var c = s.closest(".md-header__option");
            if (!c || c.getAttribute("data-md-component") !== "palette") {
                target = c || s;
                break;
            }
        }
        
        if (!target) return;

        var searchButton = document.querySelector("label[for='__search']");
        var headerInner = document.querySelector(".md-header__inner");
        
        if (searchButton && headerInner) {
             // Move only if not already before searchButton
             if (target.nextElementSibling !== searchButton) {
                 // console.log("Move Version Selector: Moving...");
                 headerInner.insertBefore(target, searchButton);
                 target.style.marginRight = "8px";
             }
        }
    }

    // Try immediately
    moveSelector();

    // Observe changes in header
    var observer = new MutationObserver(moveSelector);
    observer.observe(header, { childList: true, subtree: true });
});
