function renderTopbar(activePage) {
  const user = getUser();
  const mount = document.getElementById("topbar");
  if (!mount || !user) return;

  const links =
    user.role === "ADMIN"
      ? [
          ["dashboard", "Dashboard", "/admin/dashboard.html"],
          ["quizzes", "Quizzes", "/admin/quizzes.html"],
          ["categories", "Categories", "/admin/categories.html"],
          ["users", "Students", "/admin/users.html"],
          ["results", "Results", "/admin/results.html"],
        ]
      : [
          ["dashboard", "Dashboard", "/student/dashboard.html"],
          ["quizzes", "Quizzes", "/student/quizzes.html"],
          ["history", "History", "/student/history.html"],
          ["leaderboard", "Leaderboard", "/student/leaderboard.html"],
        ];

  mount.innerHTML = `
    <div class="brand">Quiz Platform</div>
    <nav>
      ${links.map(([key, label, href]) => `<a href="${href}" class="${key === activePage ? "active" : ""}">${label}</a>`).join("")}
      <a href="#" id="logoutLink">Log out</a>
    </nav>
  `;

  document.getElementById("logoutLink").addEventListener("click", (e) => {
    e.preventDefault();
    clearSession();
    window.location.href = "/auth/login.html";
  });
}
