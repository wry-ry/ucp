document.addEventListener("DOMContentLoaded", function() {
    // Find the version selector container
    // It is usually a .md-header__option that contains a .md-select
    var options = document.querySelectorAll(".md-header__option");
    var versionOption = null;
    
    options.forEach(function(opt) {
        if (opt.querySelector(".md-select") && !opt.hasAttribute("data-md-component")) {
            // The Palette has data-md-component="palette"
            // The Version selector usually has no data-md-component on the option wrapper
            versionOption = opt;
        }
    });

    if (versionOption) {
        var searchButton = document.querySelector("label[for='__search']");
        var headerInner = document.querySelector(".md-header__inner");
        
        if (searchButton && headerInner) {
            // Move versionOption before searchButton
            headerInner.insertBefore(versionOption, searchButton);
            // Add margin for spacing
            versionOption.style.marginRight = "8px";
        }
    }
});
