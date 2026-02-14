document.addEventListener("DOMContentLoaded", function() {
    var header = document.querySelector(".md-header");
    if (!header) return;

    function moveSelector() {
        // Find .md-select
        var select = header.querySelector(".md-select");
        if (!select) return;

        var container = select.closest(".md-header__option");
        var target = container || select;

        // Check if palette
        if (container && container.getAttribute("data-md-component") === "palette") {
             // Look for other selects
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
        }
        
        if (!target) return;

        var searchButton = document.querySelector("label[for='__search']");
        var headerInner = document.querySelector(".md-header__inner");
        
        if (searchButton && headerInner) {
             // Move if not already before searchButton
             if (target.nextElementSibling !== searchButton) {
                 // Move it
                 headerInner.insertBefore(target, searchButton);
                 
                 // Apply styles to ensure visibility
                 target.style.marginRight = "8px";
                 target.style.display = "flex"; // md-header__option is flex usually
                 target.style.visibility = "visible";
                 target.style.opacity = "1";
                 
                 // Force z-index if needed?
                 target.style.position = "relative";
                 target.style.zIndex = "10";
             }
        }
    }

    moveSelector();
    var observer = new MutationObserver(moveSelector);
    observer.observe(header, { childList: true, subtree: true });
});
