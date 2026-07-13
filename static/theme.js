(() => {
    const storageKey = "lostark-calculator-theme";
    const root = document.documentElement;
    const toggle = document.getElementById("theme-toggle");

    if (!toggle) {
        return;
    }

    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)");

    const getCurrentTheme = () => {
        if (root.dataset.theme === "light" || root.dataset.theme === "dark") {
            return root.dataset.theme;
        }
        return systemPrefersDark.matches ? "dark" : "light";
    };

    const updateButton = () => {
        const currentTheme = getCurrentTheme();
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        const icon = toggle.querySelector(".theme-icon");
        const label = toggle.querySelector(".theme-label");

        toggle.setAttribute("aria-label", `${nextTheme === "dark" ? "다크" : "라이트"} 모드로 전환`);
        toggle.setAttribute("title", `${nextTheme === "dark" ? "다크" : "라이트"} 모드로 전환`);
        if (icon) {
            icon.textContent = nextTheme === "dark" ? "☾" : "☀";
        }
        if (label) {
            label.textContent = nextTheme === "dark" ? "다크" : "라이트";
        }
    };

    toggle.addEventListener("click", () => {
        const nextTheme = getCurrentTheme() === "dark" ? "light" : "dark";
        root.dataset.theme = nextTheme;
        try {
            localStorage.setItem(storageKey, nextTheme);
        } catch (error) {
            // 저장하지 못하더라도 현재 페이지의 테마 전환은 유지한다.
        }
        updateButton();
    });

    systemPrefersDark.addEventListener("change", () => {
        if (!root.dataset.theme) {
            updateButton();
        }
    });

    updateButton();
})();
