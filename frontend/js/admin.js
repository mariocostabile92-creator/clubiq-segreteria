let adminSummary = null;
let adminUsers = [];
let adminClubs = [];

const ADMIN_API_BASE_URL = "/api";
const ADMIN_PLANS = ["free", "pro", "premium"];
const ADMIN_STATUSES = ["active", "suspended"];

document.addEventListener("DOMContentLoaded", async () => {
    const token = getAdminToken();

    if(!token){
        window.location.href = "index.html";
        return;
    }

    const refreshBtn = document.getElementById("refreshAdminBtn");
    if(refreshBtn){
        refreshBtn.addEventListener("click", loadAdminPanel);
    }

    await loadAdminPanel();
});

function getAdminToken(){
    return (
        localStorage.getItem("clubiq_token") ||
        localStorage.getItem("clubiq_access_token") ||
        localStorage.getItem("access_token") ||
        localStorage.getItem("token") ||
        localStorage.getItem("authToken") ||
        ""
    );
}

async function adminApiRequest(path, options = {}){
    const token = getAdminToken();

    if(!token){
        throw new Error("Sessione non trovata. Effettua di nuovo il login.");
    }

    const headers = {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json",
        ...(options.headers || {})
    };

    if(options.body && !headers["Content-Type"]){
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${ADMIN_API_BASE_URL}${path}`, {
        method: options.method || "GET",
        ...options,
        headers
    });

    let data = null;

    try{
        data = await response.json();
    }catch(error){
        data = null;
    }

    if(!response.ok){
        const detail = data?.detail || data?.message || response.statusText || "Errore richiesta admin";
        throw new Error(detail);
    }

    return data;
}

async function loadAdminPanel(){
    setAdminMessage("Caricamento admin panel...", "info");

    try{
        const [summary, users, clubs] = await Promise.all([
            adminApiRequest("/admin/summary"),
            adminApiRequest("/admin/users"),
            adminApiRequest("/admin/clubs")
        ]);

        adminSummary = summary || {};
        adminUsers = Array.isArray(users) ? users : [];
        adminClubs = Array.isArray(clubs) ? clubs : [];

        renderAdminSummary();
        renderAdminClubs();
        renderAdminUsers();

        setAdminMessage("Admin panel aggiornato.", "success");
    }catch(error){
        const message = error.message || "Accesso admin non autorizzato o errore caricamento.";
        setAdminMessage(message, "error");
        renderAdminError(message);
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
        tbody.innerHTML = `<tr><td colspan="8">Nessuna società registrata.</td></tr>`;
        return;
    }

    tbody.innerHTML = adminClubs.map(club => {
        const plan = club.plan || "free";
        const status = club.subscription_status || "active";
        const notes = club.admin_notes || "";

        return `
            <tr data-club-id="${club.id}">
                <td>
                    <strong>${escapeHtml(club.name || "-")}</strong>
                    <small>Codice: ${escapeHtml(club.public_code || "-")}</small>
                    <small>ID società: ${club.id}</small>
                </td>
                <td>
                    ${escapeHtml(club.email || "-")}
                    <small>${escapeHtml(club.phone || "")}</small>
                </td>
                <td>
                    <strong>${club.users_count || 0} utenti</strong>
                    <small>${club.athletes_count || 0} atleti · ${club.payments_count || 0} pagamenti</small>
                    <small>${club.certificates_count || 0} certificati</small>
                </td>
                <td><strong>${formatEuro(club.total_residual || 0)}</strong></td>
                <td>
                    <select class="admin-select" data-plan-select="${club.id}">
                        ${ADMIN_PLANS.map(item => `<option value="${item}" ${item === plan ? "selected" : ""}>${getPlanLabel(item)}</option>`).join("")}
                    </select>
                </td>
                <td>
                    <select class="admin-select" data-status-select="${club.id}">
                        ${ADMIN_STATUSES.map(item => `<option value="${item}" ${item === status ? "selected" : ""}>${getStatusLabel(item)}</option>`).join("")}
                    </select>
                </td>
                <td>
                    <textarea class="admin-notes-input" data-notes-input="${club.id}" rows="3" placeholder="Note interne cliente...">${escapeHtml(notes)}</textarea>
                </td>
                <td>
                    <button class="mini-btn success" type="button" onclick="saveClubPlan(${club.id})">Salva</button>
                </td>
            </tr>
        `;
    }).join("");
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
            <td>
                <strong>${escapeHtml(user.username || "-")}</strong>
                <small>ID ${user.id}</small>
            </td>
            <td>${escapeHtml(user.email || "-")}</td>
            <td>${escapeHtml(user.club_name || "-")}</td>
            <td><span class="admin-role">${escapeHtml(user.role || "member")}</span></td>
            <td>${user.email_verified ? "✅ Verificata" : "⚠️ Non verificata"}</td>
            <td>
                <span class="admin-plan ${escapeHtml(user.plan || "free")}">${escapeHtml(getPlanLabel(user.plan || "free"))}</span>
                ${user.subscription_status === "suspended" ? `<small class="admin-status-warning">Sospesa</small>` : ""}
            </td>
        </tr>
    `).join("");
}

async function saveClubPlan(clubId){
    const planSelect = document.querySelector(`[data-plan-select="${clubId}"]`);
    const statusSelect = document.querySelector(`[data-status-select="${clubId}"]`);
    const notesInput = document.querySelector(`[data-notes-input="${clubId}"]`);

    if(!planSelect || !statusSelect){
        setAdminMessage("Campi piano non trovati.", "error");
        return;
    }

    setAdminMessage("Salvataggio piano società...", "info");

    try{
        await adminApiRequest(`/admin/clubs/${clubId}/plan`, {
            method: "PATCH",
            body: JSON.stringify({
                plan: planSelect.value,
                subscription_status: statusSelect.value,
                admin_notes: notesInput?.value || ""
            })
        });

        await loadAdminPanel();
        setAdminMessage("Piano società aggiornato correttamente.", "success");
    }catch(error){
        setAdminMessage(error.message || "Errore durante il salvataggio del piano.", "error");
    }
}

function getPlanLabel(plan){
    if(plan === "premium") return "Premium";
    if(plan === "pro") return "Pro";
    return "Free";
}

function getStatusLabel(status){
    if(status === "suspended") return "Sospeso";
    return "Attivo";
}

function renderAdminError(message){
    const clubsTable = document.getElementById("adminClubsTable");
    const usersTable = document.getElementById("adminUsersTable");

    if(clubsTable){
        clubsTable.innerHTML = `<tr><td colspan="8">${escapeHtml(message)}</td></tr>`;
    }

    if(usersTable){
        usersTable.innerHTML = `<tr><td colspan="6">${escapeHtml(message)}</td></tr>`;
    }
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
    if(el){
        el.textContent = value;
    }
}

function formatEuro(value){
    const number = Number(value || 0);
    return number.toLocaleString("it-IT", {
        style: "currency",
        currency: "EUR"
    });
}

function escapeHtml(value){
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
