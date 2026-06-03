let adminSummary = null;
let adminUsers = [];
let adminClubs = [];

document.addEventListener("DOMContentLoaded", async () => {
    if(typeof isLoggedIn === "function" && !isLoggedIn()){
        window.location.href = "index.html";
        return;
    }

    const refreshBtn = document.getElementById("refreshAdminBtn");
    if(refreshBtn) refreshBtn.addEventListener("click", loadAdminPanel);

    await loadAdminPanel();
});

async function loadAdminPanel(){
    setAdminMessage("Caricamento admin panel...", "info");

    try{
        const [summary, users, clubs] = await Promise.all([
            apiRequest("/admin/summary"),
            apiRequest("/admin/users"),
            apiRequest("/admin/clubs")
        ]);

        adminSummary = summary;
        adminUsers = Array.isArray(users) ? users : [];
        adminClubs = Array.isArray(clubs) ? clubs : [];

        renderAdminSummary();
        renderAdminClubs();
        renderAdminUsers();
        setAdminMessage("Admin panel aggiornato.", "success");
    }catch(error){
        setAdminMessage(error.message || "Accesso admin non autorizzato o errore caricamento.", "error");
        renderAdminError(error.message || "Errore");
    }
}

function renderAdminSummary(){
    if(!adminSummary) return;
    setText("adminUsersCount", adminSummary.users_count || 0);
    setText("adminClubsCount", adminSummary.clubs_count || 0);
    setText("adminAthletesCount", adminSummary.athletes_count || 0);
    setText("adminPaymentsCount", adminSummary.payments_count || 0);
    setText("adminResidualCount", formatEuro(adminSummary.total_residual || 0));
}

function renderAdminClubs(){
    const tbody = document.getElementById("adminClubsTable");
    if(!tbody) return;

    if(!adminClubs.length){
        tbody.innerHTML = `<tr><td colspan="7">Nessuna società registrata.</td></tr>`;
        return;
    }

    tbody.innerHTML = adminClubs.map(club => `
        <tr>
            <td><strong>${escapeHtml(club.name || "-")}</strong><small>Codice: ${escapeHtml(club.public_code || "-")}</small></td>
            <td>${escapeHtml(club.email || "-")}<small>${escapeHtml(club.phone || "")}</small></td>
            <td>${club.users_count || 0}</td>
            <td>${club.athletes_count || 0}</td>
            <td>${club.payments_count || 0}</td>
            <td><strong>${formatEuro(club.total_residual || 0)}</strong></td>
            <td><span class="admin-plan">${escapeHtml(club.plan || "free")}</span></td>
        </tr>
    `).join("");
}

function renderAdminUsers(){
    const tbody = document.getElementById("adminUsersTable");
    if(!tbody) return;

    if(!adminUsers.length){
        tbody.innerHTML = `<tr><td colspan="6">Nessun utente registrato.</td></tr>`;
        return;
    }

    tbody.innerHTML = adminUsers.map(user => `
        <tr>
            <td><strong>${escapeHtml(user.username || "-")}</strong><small>ID ${user.id}</small></td>
            <td>${escapeHtml(user.email || "-")}</td>
            <td>${escapeHtml(user.club_name || "-")}</td>
            <td><span class="admin-role">${escapeHtml(user.role || "member")}</span></td>
            <td>${user.email_verified ? "✅ Verificata" : "⚠️ Non verificata"}</td>
            <td><span class="admin-plan">${escapeHtml(user.plan || "free")}</span></td>
        </tr>
    `).join("");
}

function renderAdminError(message){
    const clubsTable = document.getElementById("adminClubsTable");
    const usersTable = document.getElementById("adminUsersTable");
    if(clubsTable) clubsTable.innerHTML = `<tr><td colspan="7">${escapeHtml(message)}</td></tr>`;
    if(usersTable) usersTable.innerHTML = `<tr><td colspan="6">${escapeHtml(message)}</td></tr>`;
}

function setAdminMessage(message, type = "info"){
    const box = document.getElementById("adminMessage");
    if(!box) return;
    box.textContent = message;
    box.className = `message ${type}`;
    box.classList.remove("hidden");
}

function setText(id, value){
    const el = document.getElementById(id);
    if(el) el.textContent = value;
}

function formatEuro(value){
    const number = Number(value || 0);
    return number.toLocaleString("it-IT", { style:"currency", currency:"EUR" });
}

function escapeHtml(value){
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
