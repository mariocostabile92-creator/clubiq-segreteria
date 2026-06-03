/*
  ClubIQ Segreteria - Dashboard
  V2.3.1 WhatsApp V1.3.1 Hotfix Storico
  Dashboard + Atleti + Pagamenti + Certificati + Scheda atleta + Filtri + Azioni rapide + Modifica + Export CSV
*/

let cachedAthletes = [];
let cachedPayments = [];
let cachedCertificates = [];
let cachedParentRequests = [];
let cachedClub = null;
let currentUser = null;
let openedAthleteId = null;
let editingAthleteId = null;
let editingPaymentId = null;
let editingCertificateId = null;

document.addEventListener("DOMContentLoaded", async () => {
    if(!isLoggedIn()){
        window.location.href = "index.html";
        return;
    }

    bindDashboardActions();
    await refreshAll();
    renderCommunicationHistory();
});

function bindDashboardActions(){
    const logoutBtn = document.getElementById("logoutBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const generateSecretaryReportPdfBtn = document.getElementById("generateSecretaryReportPdfBtn");
    const addAthleteForm = document.getElementById("addAthleteForm");
    const addPaymentForm = document.getElementById("addPaymentForm");
    const addCertificateForm = document.getElementById("addCertificateForm");
    const closeAthleteDetailBtn = document.getElementById("closeAthleteDetailBtn");
    const quickPaymentBtn = document.getElementById("quickPaymentBtn");
    const quickCertificateBtn = document.getElementById("quickCertificateBtn");
    const copyRegistrationLinkBtn = document.getElementById("copyRegistrationLinkBtn");
    const openRegistrationLinkBtn = document.getElementById("openRegistrationLinkBtn");
    const clubSettingsForm = document.getElementById("clubSettingsForm");
    const regenerateClubCodeBtn = document.getElementById("regenerateClubCodeBtn");
    const resendVerificationBtn = document.getElementById("resendVerificationBtn");
    const todayChecksRefreshBtn = document.getElementById("todayChecksRefreshBtn");
    const sendQuickRegistrationLinkBtn = document.getElementById("sendQuickRegistrationLinkBtn");
    const sendQuickDocumentsBtn = document.getElementById("sendQuickDocumentsBtn");
    const sendQuickCustomBtn = document.getElementById("sendQuickCustomBtn");
    const clearCommunicationHistoryBtn = document.getElementById("clearCommunicationHistoryBtn");
    const exportCommunicationHistoryCsvBtn = document.getElementById("exportCommunicationHistoryCsvBtn");
    const communicationHistorySearchInput = document.getElementById("communicationHistorySearchInput");
    const communicationHistoryTypeFilter = document.getElementById("communicationHistoryTypeFilter");

    const cancelPaymentEditBtn = document.getElementById("cancelPaymentEditBtn");
    const cancelCertificateEditBtn = document.getElementById("cancelCertificateEditBtn");
    const exportPaymentsCsvBtn = document.getElementById("exportPaymentsCsvBtn");
    const exportCertificatesCsvBtn = document.getElementById("exportCertificatesCsvBtn");
    const refreshParentRequestsBtn = document.getElementById("refreshParentRequestsBtn");
    const parentRequestSearchInput = document.getElementById("parentRequestSearchInput");
    const parentRequestStatusFilter = document.getElementById("parentRequestStatusFilter");
    const parentRequestGroupFilter = document.getElementById("parentRequestGroupFilter");

    const athleteSearchInput = document.getElementById("athleteSearchInput");
    const athleteGroupFilter = document.getElementById("athleteGroupFilter");
    const athleteStatusFilter = document.getElementById("athleteStatusFilter");

    const paymentSearchInput = document.getElementById("paymentSearchInput");
    const paymentGroupFilter = document.getElementById("paymentGroupFilter");
    const paymentStatusFilter = document.getElementById("paymentStatusFilter");

    const certificateSearchInput = document.getElementById("certificateSearchInput");
    const certificateGroupFilter = document.getElementById("certificateGroupFilter");
    const certificateStatusFilter = document.getElementById("certificateStatusFilter");

    if(logoutBtn){
        logoutBtn.addEventListener("click", () => {
            clearToken();
            window.location.href = "index.html";
        });
    }

    if(refreshBtn){
        refreshBtn.addEventListener("click", refreshAll);
    }

    if(generateSecretaryReportPdfBtn){
        generateSecretaryReportPdfBtn.addEventListener("click", generateSecretaryReportPdf);
    }

    if(resendVerificationBtn){
        resendVerificationBtn.addEventListener("click", resendVerificationEmail);
    }

    if(todayChecksRefreshBtn){
        todayChecksRefreshBtn.addEventListener("click", refreshTodayChecks);
    }

    if(sendQuickRegistrationLinkBtn){
        sendQuickRegistrationLinkBtn.addEventListener("click", sendQuickRegistrationLinkWhatsApp);
    }

    if(sendQuickDocumentsBtn){
        sendQuickDocumentsBtn.addEventListener("click", sendQuickDocumentsWhatsApp);
    }

    if(sendQuickCustomBtn){
        sendQuickCustomBtn.addEventListener("click", sendQuickCustomWhatsApp);
    }

    if(clearCommunicationHistoryBtn){
        clearCommunicationHistoryBtn.addEventListener("click", clearCommunicationHistory);
    }

    if(exportCommunicationHistoryCsvBtn){
        exportCommunicationHistoryCsvBtn.addEventListener("click", exportCommunicationHistoryCsv);
    }

    [communicationHistorySearchInput, communicationHistoryTypeFilter].filter(Boolean).forEach(input => {
        input.addEventListener("input", renderCommunicationHistory);
        input.addEventListener("change", renderCommunicationHistory);
    });

    if(addAthleteForm){
        addAthleteForm.addEventListener("submit", handleAddAthlete);
    }

    if(addPaymentForm){
        addPaymentForm.addEventListener("submit", handleAddPayment);
    }

    if(addCertificateForm){
        addCertificateForm.addEventListener("submit", handleAddCertificate);
    }

    if(cancelPaymentEditBtn){
        cancelPaymentEditBtn.addEventListener("click", resetPaymentForm);
    }

    if(cancelCertificateEditBtn){
        cancelCertificateEditBtn.addEventListener("click", resetCertificateForm);
    }

    if(exportPaymentsCsvBtn){
        exportPaymentsCsvBtn.addEventListener("click", exportPaymentsCsv);
    }

    if(exportCertificatesCsvBtn){
        exportCertificatesCsvBtn.addEventListener("click", exportCertificatesCsv);
    }

    if(refreshParentRequestsBtn){
        refreshParentRequestsBtn.addEventListener("click", loadParentRequestsList);
    }

    [parentRequestSearchInput, parentRequestStatusFilter, parentRequestGroupFilter].filter(Boolean).forEach(input => {
        input.addEventListener("input", renderParentRequestsList);
        input.addEventListener("change", renderParentRequestsList);
    });

    if(closeAthleteDetailBtn){
        closeAthleteDetailBtn.addEventListener("click", closeAthleteDetail);
    }

    if(quickPaymentBtn){
        quickPaymentBtn.addEventListener("click", quickCreatePaymentForOpenedAthlete);
    }

    if(quickCertificateBtn){
        quickCertificateBtn.addEventListener("click", quickCreateCertificateForOpenedAthlete);
    }

    if(copyRegistrationLinkBtn){
        copyRegistrationLinkBtn.addEventListener("click", copyRegistrationLink);
    }

    if(openRegistrationLinkBtn){
        openRegistrationLinkBtn.addEventListener("click", openRegistrationLink);
    }

    if(clubSettingsForm){
        clubSettingsForm.addEventListener("submit", handleUpdateClubSettings);
    }

    if(regenerateClubCodeBtn){
        regenerateClubCodeBtn.addEventListener("click", handleRegenerateClubCode);
    }

    [athleteSearchInput, athleteGroupFilter, athleteStatusFilter].filter(Boolean).forEach(input => {
        input.addEventListener("input", renderAthletesList);
        input.addEventListener("change", renderAthletesList);
    });

    [paymentSearchInput, paymentGroupFilter, paymentStatusFilter].filter(Boolean).forEach(input => {
        input.addEventListener("input", renderPaymentsList);
        input.addEventListener("change", renderPaymentsList);
    });

    [certificateSearchInput, certificateGroupFilter, certificateStatusFilter].filter(Boolean).forEach(input => {
        input.addEventListener("input", renderCertificatesList);
        input.addEventListener("change", renderCertificatesList);
    });
}


async function refreshTodayChecks(){
    const btn = document.getElementById("todayChecksRefreshBtn");

    if(btn){
        btn.disabled = true;
        btn.textContent = "Aggiornamento...";
    }

    setDashboardMessage("Aggiornamento controlli rapidi...", "info");

    try{
        await refreshAll();
        const totalChecks = getTodayChecksTotal();

        if(totalChecks === 0){
            setDashboardMessage("Controlli aggiornati: tutto sotto controllo.", "success");
        }else if(totalChecks === 1){
            setDashboardMessage("Controlli aggiornati: hai 1 attività da controllare.", "success");
        }else{
            setDashboardMessage(`Controlli aggiornati: hai ${totalChecks} attività da controllare.`, "success");
        }
    }catch(error){
        setDashboardMessage(error.message || "Errore durante l'aggiornamento dei controlli.", "error");
    }finally{
        if(btn){
            btn.disabled = false;
            btn.textContent = "Aggiorna controlli";
        }
    }
}

async function refreshAll(){
    await loadCurrentUser();
    await loadMyClub();
    await loadDashboard();
    await loadAthletesPreview();
    await loadPaymentsList();
    await loadCertificatesList();
    await loadParentRequestsList();

    renderAthletesList();
    renderPaymentsList();
    renderCertificatesList();
    renderTodayChecks();

    if(openedAthleteId){
        openAthleteDetail(openedAthleteId, false);
    }

    renderCommunicationHistory();
}

async function loadCurrentUser(){
    try{
        currentUser = await apiRequest("/auth/me");
        renderEmailVerificationState();
    }catch(error){
        currentUser = null;

        if(String(error.message || "").toLowerCase().includes("not authenticated")){
            clearToken();
            window.location.href = "index.html";
            return;
        }

        setDashboardMessage("Impossibile verificare lo stato account.", "error");
    }
}

function renderEmailVerificationState(){
    const banner = document.getElementById("emailVerificationBanner");
    const emailBox = document.getElementById("currentUserEmail");

    if(emailBox){
        emailBox.textContent = currentUser?.email || "Email non disponibile";
    }

    if(!banner) return;

    if(currentUser && currentUser.email_verified === false){
        banner.classList.remove("hidden");
    }else{
        banner.classList.add("hidden");
    }
}

function isEmailVerified(){
    return !!currentUser?.email_verified;
}

function requireVerifiedEmail(actionLabel = "questa funzione"){
    if(isEmailVerified()){
        return true;
    }

    setDashboardMessage(
        `Verifica la tua email prima di usare ${actionLabel}. Controlla la posta oppure reinvia il link di verifica.`,
        "error"
    );

    const banner = document.getElementById("emailVerificationBanner");
    if(banner){
        banner.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    return false;
}

async function resendVerificationEmail(){
    if(!currentUser?.email){
        setDashboardMessage("Email account non disponibile.", "error");
        return;
    }

    setDashboardMessage("Invio nuova email di verifica...", "info");

    try{
        const data = await apiRequest("/auth/resend-verification", {
            method: "POST",
            body: JSON.stringify({
                email: currentUser.email
            })
        });

        setDashboardMessage(data.message || "Email di verifica inviata.", "success");
    }catch(error){
        setDashboardMessage(error.message || "Errore durante l'invio della verifica email.", "error");
    }
}

async function loadMyClub(){
    try{
        cachedClub = await apiRequest("/clubs/me");
        renderClubRegistrationLink();
    }catch(error){
        setText("clubNameBox", "Società non disponibile");
        setText("clubPublicCodeBox", "-");

        const input = document.getElementById("clubRegistrationLink");
        if(input){
            input.value = "Link non disponibile";
        }
    }
}

function renderClubRegistrationLink(){
    if(!cachedClub) return;

    const publicCode = cachedClub.public_code || "";
    const link = publicCode
        ? `${window.location.origin}/iscrizione.html?club=${encodeURIComponent(publicCode)}`
        : "Codice iscrizione non disponibile";

    setText("clubNameBox", cachedClub.name || "Società");
    setText("clubPublicCodeBox", publicCode || "-");
    fillClubSettingsForm();

    const input = document.getElementById("clubRegistrationLink");
    if(input){
        input.value = link;
    }
}

function getRegistrationLinkValue(){
    const input = document.getElementById("clubRegistrationLink");

    if(!input || !input.value || input.value.includes("non disponibile") || input.value.includes("Caricamento")){
        return null;
    }

    return input.value;
}

function openRegistrationLink(){
    if(!requireVerifiedEmail("il modulo iscrizione genitori")){
        return;
    }

    const link = getRegistrationLinkValue();

    if(!link){
        setDashboardMessage("Link iscrizione non disponibile.", "error");
        return;
    }

    window.open(link, "_blank", "noopener,noreferrer");
    setDashboardMessage("Modulo iscrizione aperto in una nuova scheda.", "success");
}

async function copyRegistrationLink(){
    if(!requireVerifiedEmail("il link iscrizione genitori")){
        return;
    }

    const input = document.getElementById("clubRegistrationLink");
    const link = getRegistrationLinkValue();

    if(!input || !link){
        setDashboardMessage("Link iscrizione non disponibile.", "error");
        return;
    }

    try{
        await navigator.clipboard.writeText(link);
        setDashboardMessage("Link iscrizione copiato. Puoi inviarlo ai genitori.", "success");
    }catch(error){
        input.select();
        document.execCommand("copy");
        setDashboardMessage("Link iscrizione copiato.", "success");
    }
}

function fillClubSettingsForm(){
    if(!cachedClub) return;

    setInputValue("clubNameInput", cachedClub.name || "");
    setInputValue("clubEmailInput", cachedClub.email || "");
    setInputValue("clubPhoneInput", cachedClub.phone || "");
    setInputValue("clubAddressInput", cachedClub.address || "");
    setInputValue("clubPresidentInput", cachedClub.president || "");
    setInputValue("clubSecretaryInput", cachedClub.secretary || "");
}

async function handleUpdateClubSettings(event){
    event.preventDefault();

    if(!requireVerifiedEmail("la modifica dei dati società")){
        return;
    }

    const payload = {
        name: document.getElementById("clubNameInput").value.trim(),
        email: document.getElementById("clubEmailInput").value.trim() || null,
        phone: document.getElementById("clubPhoneInput").value.trim() || null,
        address: document.getElementById("clubAddressInput").value.trim() || null,
        president: document.getElementById("clubPresidentInput").value.trim() || null,
        secretary: document.getElementById("clubSecretaryInput").value.trim() || null
    };

    if(!payload.name){
        setDashboardMessage("Inserisci il nome società.", "error");
        return;
    }

    setDashboardMessage("Salvataggio dati società...", "info");

    try{
        cachedClub = await apiRequest("/clubs/me", {
            method: "PATCH",
            body: JSON.stringify(payload)
        });

        renderClubRegistrationLink();
        setDashboardMessage("Dati società aggiornati correttamente.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function handleRegenerateClubCode(){
    if(!requireVerifiedEmail("la rigenerazione del codice iscrizione")){
        return;
    }

    if(!confirm("Vuoi rigenerare il codice iscrizione partendo dal nome società attuale? Il vecchio link non sarà più valido.")){
        return;
    }

    setDashboardMessage("Rigenerazione codice iscrizione...", "info");

    try{
        cachedClub = await apiRequest("/clubs/me/regenerate-code", {
            method: "PATCH"
        });

        renderClubRegistrationLink();
        setDashboardMessage("Codice iscrizione rigenerato. Copia il nuovo link e invialo ai genitori.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

function setInputValue(id, value){
    const el = document.getElementById(id);
    if(el) el.value = value ?? "";
}

async function loadDashboard(){
    setDashboardMessage("Caricamento dashboard...", "info");

    try{
        const summary = await apiRequest("/dashboard/summary");

        setText("athletesCount", summary.athletes_count ?? 0);
        setText("totalResiduo", formatEuro(summary.total_residuo ?? 0));
        setText("overduePayments", summary.quote_scadute ?? 0);
        setText("expiredCertificates", summary.certificati_scaduti ?? 0);
        setText("expiringCertificates", summary.certificati_in_scadenza ?? 0);

        setDashboardMessage("Dashboard aggiornata.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function loadParentRequestsList(){
    const list = document.getElementById("parentRequestsList");
    if(!list) return;

    list.innerHTML = `<div class="empty">Caricamento richieste...</div>`;

    try{
        cachedParentRequests = await apiRequest("/parent-requests/");
        populateParentRequestGroupFilter();
        renderParentRequestsList();
    }catch(error){
        list.innerHTML = `<div class="empty error">${escapeHtml(error.message)}</div>`;
        setText("pendingRequestsCount", 0);
        setText("approvedRequestsCount", 0);
        setText("rejectedRequestsCount", 0);
    }
}

function populateParentRequestGroupFilter(){
    const select = document.getElementById("parentRequestGroupFilter");
    if(!select) return;

    const currentValue = select.value;
    const groups = [...new Set(cachedParentRequests.map(item => item.requested_group || "Senza gruppo"))]
        .filter(Boolean)
        .sort((a,b)=>a.localeCompare(b,"it"));

    select.innerHTML = `<option value="">Tutti i gruppi</option>` + groups.map(group => `<option value="${escapeHtml(group)}">${escapeHtml(group)}</option>`).join("");

    if(currentValue && groups.includes(currentValue)){
        select.value = currentValue;
    }
}

function renderParentRequestsList(){
    const list = document.getElementById("parentRequestsList");
    if(!list) return;

    setText("pendingRequestsCount", cachedParentRequests.filter(item => item.status === "pending").length);
    setText("approvedRequestsCount", cachedParentRequests.filter(item => item.status === "approved").length);
    setText("rejectedRequestsCount", cachedParentRequests.filter(item => item.status === "rejected").length);

    if(!cachedParentRequests.length){
        list.innerHTML = `<div class="empty">Nessuna richiesta genitore presente.</div>`;
        setText("parentRequestsFilterSummary", "Richieste visualizzate: 0");
        return;
    }

    const filtered = getFilteredParentRequests();
    setText("parentRequestsFilterSummary", `${filtered.length} richieste visualizzate`);

    if(!filtered.length){
        list.innerHTML = `<div class="empty">Nessuna richiesta trovata con questi filtri.</div>`;
        return;
    }

    list.innerHTML = filtered.map(request => {
        const status = getParentRequestStatus(request.status);
        const athleteName = `${request.athlete_first_name || ""} ${request.athlete_last_name || ""}`.trim();

        return `
            <article class="data-card request-card">
                <div>
                    <strong>${escapeHtml(athleteName || "Atleta senza nome")}</strong>
                    <span>Gruppo richiesto: ${escapeHtml(request.requested_group || "Senza gruppo")} · Nato il: ${formatDate(request.athlete_birth_date)}</span>
                    <span>Genitore: ${escapeHtml(request.parent_name || "Non indicato")} · ${escapeHtml(request.parent_phone || "Telefono non indicato")} · ${escapeHtml(request.parent_email || "Email non indicata")}</span>
                    ${request.notes ? `<span>Note: ${escapeHtml(request.notes)}</span>` : ""}
                    ${(request.certificate_file_url || request.payment_receipt_url) ? `
                        <div class="request-documents">
                            <span class="request-documents-title">Documenti caricati</span>
                            <div class="request-documents-actions">
                                ${request.certificate_file_url ? `
                                    <a class="document-btn document-btn-certificate" href="${escapeHtml(request.certificate_file_url)}" target="_blank" rel="noopener noreferrer">
                                        <span class="document-btn-icon">📄</span>
                                        <span>Apri certificato medico</span>
                                    </a>
                                ` : ""}
                                ${request.payment_receipt_url ? `
                                    <a class="document-btn document-btn-receipt" href="${escapeHtml(request.payment_receipt_url)}" target="_blank" rel="noopener noreferrer">
                                        <span class="document-btn-icon">🧾</span>
                                        <span>Apri ricevuta pagamento</span>
                                    </a>
                                ` : ""}
                            </div>
                        </div>
                    ` : ""}
                    ${request.review_note ? `<span>Esito: ${escapeHtml(request.review_note)}</span>` : ""}
                </div>
                <div class="data-card-right">
                    <b class="${status.className}">${status.label}</b>
                    <small>Richiesta #${request.id}</small>
                    <div class="card-actions">
                        ${request.parent_phone ? `<button type="button" class="mini-btn whatsapp" onclick="openWhatsAppParentRequest(${request.id}, 'generic')">💬 WhatsApp</button>` : ""}
                        ${request.parent_phone ? `<button type="button" class="mini-btn whatsapp" onclick="openWhatsAppParentRequest(${request.id}, 'confirm')">✅ Conferma</button>` : ""}
                        ${request.status === "pending" ? `
                            <button type="button" class="mini-btn success" onclick="approveParentRequest(${request.id})">Approva</button>
                            <button type="button" class="mini-btn" onclick="rejectParentRequest(${request.id})">Rifiuta</button>
                        ` : ""}
                        ${request.status !== "approved" ? `<button type="button" class="mini-btn danger" onclick="deleteParentRequest(${request.id})">Elimina</button>` : ""}
                    </div>
                </div>
            </article>`;
    }).join("");
}

function getFilteredParentRequests(){
    const search = (document.getElementById("parentRequestSearchInput")?.value || "").trim().toLowerCase();
    const statusFilter = document.getElementById("parentRequestStatusFilter")?.value || "";
    const group = document.getElementById("parentRequestGroupFilter")?.value || "";

    return cachedParentRequests.filter(request => {
        const haystack = [
            request.athlete_first_name,
            request.athlete_last_name,
            request.requested_group,
            request.parent_name,
            request.parent_phone,
            request.parent_email,
            request.notes,
            request.review_note,
            request.status
        ].join(" ").toLowerCase();

        return (!search || haystack.includes(search)) &&
               (!statusFilter || request.status === statusFilter) &&
               (!group || (request.requested_group || "Senza gruppo") === group);
    });
}

function getParentRequestStatus(status){
    if(status === "approved") return { label:"Approvata", className:"status-success" };
    if(status === "rejected") return { label:"Rifiutata", className:"status-danger" };
    return { label:"In attesa", className:"status-warning" };
}

async function approveParentRequest(requestId){
    if(!requireVerifiedEmail("l'approvazione delle richieste")){
        return;
    }

    if(!confirm("Vuoi approvare questa richiesta e creare automaticamente l'atleta?")){
        return;
    }

    setDashboardMessage("Approvazione richiesta...", "info");

    try{
        await apiRequest(`/parent-requests/${requestId}/approve`, { method:"PATCH" });
        await refreshAll();
        setDashboardMessage("Richiesta approvata. Atleta creato automaticamente.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function rejectParentRequest(requestId){
    if(!requireVerifiedEmail("la gestione delle richieste")){
        return;
    }

    const reason = prompt("Motivo del rifiuto o nota per la segreteria:", "Richiesta rifiutata.");
    if(reason === null) return;

    setDashboardMessage("Rifiuto richiesta...", "info");

    try{
        await apiRequest(`/parent-requests/${requestId}/reject`, {
            method:"PATCH",
            body:JSON.stringify({ review_note: reason || "Richiesta rifiutata." })
        });

        await loadParentRequestsList();
        setDashboardMessage("Richiesta rifiutata.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function deleteParentRequest(requestId){
    if(!requireVerifiedEmail("l'eliminazione delle richieste")){
        return;
    }

    if(!confirm("Vuoi eliminare questa richiesta?")){
        return;
    }

    setDashboardMessage("Eliminazione richiesta...", "info");

    try{
        await apiRequest(`/parent-requests/${requestId}`, { method:"DELETE" });
        await loadParentRequestsList();
        setDashboardMessage("Richiesta eliminata.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function loadAthletesPreview(){
    const list = document.getElementById("athletesList");

    if(list){
        list.innerHTML = `<div class="empty">Caricamento atleti...</div>`;
    }

    try{
        cachedAthletes = await apiRequest("/athletes/");
        populateAthleteSelects();
        populateAllGroupFilters();
        renderAthletesList();
    }catch(error){
        if(list){
            list.innerHTML = `<div class="empty error">${escapeHtml(error.message)}</div>`;
        }
    }
}

function renderAthletesList(){
    const list = document.getElementById("athletesList");
    if(!list) return;

    if(!cachedAthletes.length){
        list.innerHTML = `<div class="empty">Nessun atleta inserito.</div>`;
        return;
    }

    const search = (document.getElementById("athleteSearchInput")?.value || "").trim().toLowerCase();
    const group = document.getElementById("athleteGroupFilter")?.value || "";
    const status = document.getElementById("athleteStatusFilter")?.value || "";

    const filtered = cachedAthletes.filter(athlete => {
        const athleteStatus = getAthleteAdminStatus(athlete);

        const haystack = [
            athlete.first_name,
            athlete.last_name,
            athlete.group_name,
            athlete.parent_name_1,
            athlete.parent_phone_1,
            athlete.parent_email_1,
            athlete.email,
            athlete.phone
        ].join(" ").toLowerCase();

        return (!search || haystack.includes(search)) &&
               (!group || (athlete.group_name || "Senza gruppo") === group) &&
               (!status || athleteStatus.key === status);
    });

    if(!filtered.length){
        list.innerHTML = `<div class="empty">Nessun atleta trovato con questi filtri.</div>`;
        return;
    }

    list.innerHTML = filtered.map(athlete => {
        const status = getAthleteAdminStatus(athlete);

        return `
            <article class="athlete-card">
                <div>
                    <strong>${escapeHtml(athlete.first_name)} ${escapeHtml(athlete.last_name)}</strong>
                    <span>${escapeHtml(athlete.group_name || "Senza gruppo")}</span>
                    <small>${escapeHtml(athlete.parent_name_1 || athlete.email || "Nessun contatto")}</small>
                </div>

                <div class="card-actions">
                    <span class="status-badge ${status.className}">${status.label}</span>
                    ${athlete.parent_phone_1 || athlete.phone ? `<button type="button" class="mini-btn whatsapp" onclick="openWhatsAppAthlete(${athlete.id}, 'generic')">💬 WhatsApp</button>` : ""}
                    <button type="button" class="mini-btn" onclick="openAthleteDetail(${athlete.id})">Apri scheda</button>
                    <button type="button" class="mini-btn" onclick="fillAthleteForm(${athlete.id})">Modifica</button>
                    <button type="button" class="mini-btn danger" onclick="deleteAthlete(${athlete.id})">Elimina</button>
                </div>
            </article>
        `;
    }).join("");
}

function populateAllGroupFilters(){
    const selects = [
        document.getElementById("athleteGroupFilter"),
        document.getElementById("paymentGroupFilter"),
        document.getElementById("certificateGroupFilter")
    ].filter(Boolean);

    const groups = [...new Set(cachedAthletes.map(athlete => athlete.group_name || "Senza gruppo"))]
        .filter(Boolean)
        .sort((a, b) => a.localeCompare(b, "it"));

    selects.forEach(select => {
        const currentValue = select.value;

        select.innerHTML = `<option value="">Tutti i gruppi</option>` + groups.map(group => `
            <option value="${escapeHtml(group)}">${escapeHtml(group)}</option>
        `).join("");

        if(currentValue && groups.includes(currentValue)){
            select.value = currentValue;
        }
    });
}

function populateAthleteSelects(){
    const selects = [
        document.getElementById("paymentAthleteId"),
        document.getElementById("certificateAthleteId")
    ].filter(Boolean);

    selects.forEach(select => {
        const currentValue = select.value;

        select.innerHTML = `<option value="">Seleziona atleta</option>` + cachedAthletes.map(athlete => `
            <option value="${athlete.id}">
                ${escapeHtml(athlete.first_name)} ${escapeHtml(athlete.last_name)} - ${escapeHtml(athlete.group_name || "Senza gruppo")}
            </option>
        `).join("");

        if(currentValue){
            select.value = currentValue;
        }
    });
}

async function loadPaymentsList(){
    const list = document.getElementById("paymentsList");
    if(!list) return;

    list.innerHTML = `<div class="empty">Caricamento pagamenti...</div>`;

    try{
        cachedPayments = await apiRequest("/payments/");
        renderPaymentsList();
    }catch(error){
        list.innerHTML = `<div class="empty error">${escapeHtml(error.message)}</div>`;
    }
}

function renderPaymentsList(){
    const list = document.getElementById("paymentsList");
    if(!list) return;

    if(!cachedPayments.length){
        list.innerHTML = `<div class="empty">Nessun pagamento inserito.</div>`;
        setText("paymentsFilterSummary", "");
        return;
    }

    const filtered = getFilteredPayments();

    const totalDue = filtered.reduce((sum, payment) => sum + Number(payment.amount_due || 0), 0);
    const totalPaid = filtered.reduce((sum, payment) => sum + Number(payment.amount_paid || 0), 0);
    const totalResidual = filtered.reduce((sum, payment) => {
        return sum + Math.max(0, Number(payment.amount_due || 0) - Number(payment.amount_paid || 0));
    }, 0);

    setText(
        "paymentsFilterSummary",
        `${filtered.length} pagamenti visualizzati · Dovuto ${formatEuro(totalDue)} · Incassato ${formatEuro(totalPaid)} · Residuo ${formatEuro(totalResidual)}`
    );

    if(!filtered.length){
        list.innerHTML = `<div class="empty">Nessun pagamento trovato con questi filtri.</div>`;
        return;
    }

    list.innerHTML = filtered.map(payment => {
        const athlete = findAthlete(payment.athlete_id);
        const residuo = Number(payment.amount_due || 0) - Number(payment.amount_paid || 0);
        const isPaid = residuo <= 0 || payment.status === "paid";
        const paymentState = getPaymentStatusKey(payment);
        const stateLabel = paymentState === "paid" ? "Pagato" : paymentState === "overdue" ? "Scaduto" : "Aperto";

        return `
            <article class="data-card">
                <div>
                    <strong>${escapeHtml(athlete)}</strong>
                    <span>Dovuto: ${formatEuro(payment.amount_due || 0)} · Pagato: ${formatEuro(payment.amount_paid || 0)} · Scadenza: ${formatDate(payment.due_date)}</span>
                    <span>Metodo: ${escapeHtml(payment.method || "Non indicato")}</span>
                </div>

                <div class="data-card-right">
                    <b class="${isPaid ? "status-success" : paymentState === "overdue" ? "status-danger" : "status-warning"}">
                        ${isPaid ? "Pagato" : formatEuro(residuo)}
                    </b>
                    <small>${stateLabel}</small>

                    <div class="card-actions">
                        ${!isPaid ? `<button type="button" class="mini-btn whatsapp" onclick="openWhatsAppPayment(${payment.id})">💸 Sollecito</button>` : ""}
                        <button type="button" class="mini-btn" onclick="fillPaymentForm(${payment.id})">Modifica</button>

                        ${!isPaid ? `
                            <button type="button" class="mini-btn success" onclick="markPaymentPaid(${payment.id})">
                                Segna pagato
                            </button>
                        ` : ""}

                        <button type="button" class="mini-btn danger" onclick="deletePayment(${payment.id})">Elimina</button>
                    </div>
                </div>
            </article>
        `;
    }).join("");
}

async function loadCertificatesList(){
    const list = document.getElementById("certificatesList");
    if(!list) return;

    list.innerHTML = `<div class="empty">Caricamento certificati...</div>`;

    try{
        cachedCertificates = await apiRequest("/certificates/");
        renderCertificatesList();
    }catch(error){
        list.innerHTML = `<div class="empty error">${escapeHtml(error.message)}</div>`;
    }
}

function renderCertificatesList(){
    const list = document.getElementById("certificatesList");
    if(!list) return;

    if(!cachedCertificates.length){
        list.innerHTML = `<div class="empty">Nessun certificato inserito.</div>`;
        setText("certificatesFilterSummary", "");
        return;
    }

    const filtered = getFilteredCertificates();

    setText("certificatesFilterSummary", `${filtered.length} certificati visualizzati`);

    if(!filtered.length){
        list.innerHTML = `<div class="empty">Nessun certificato trovato con questi filtri.</div>`;
        return;
    }

    list.innerHTML = filtered.map(cert => {
        const athlete = findAthlete(cert.athlete_id);
        const status = getCertificateDisplayStatus(cert);

        return `
            <article class="data-card">
                <div>
                    <strong>${escapeHtml(athlete)}</strong>
                    <span>${escapeHtml(cert.type)} · Scade: ${formatDate(cert.expiry_date)}</span>
                    <span>Stato salvato: ${escapeHtml(cert.status || "valid")}</span>
                </div>

                <div class="data-card-right">
                    <b class="${status.className}">${status.label}</b>
                    <small>Certificato</small>

                    <div class="card-actions">
                        ${status.label !== "Valido" ? `<button type="button" class="mini-btn whatsapp" onclick="openWhatsAppCertificate(${cert.id})">📄 Promemoria</button>` : ""}
                        ${status.label !== "Valido" ? `
                            <button type="button" class="mini-btn success" onclick="markCertificateValid(${cert.id})">
                                Segna valido
                            </button>
                        ` : ""}

                        <button type="button" class="mini-btn" onclick="fillCertificateForm(${cert.id})">Modifica</button>
                        <button type="button" class="mini-btn danger" onclick="deleteCertificate(${cert.id})">Elimina</button>
                    </div>
                </div>
            </article>
        `;
    }).join("");
}

/* =========================
   Form e azioni atleti
========================= */

function fillAthleteForm(athleteId){
    const athlete = cachedAthletes.find(item => Number(item.id) === Number(athleteId));

    if(!athlete){
        setDashboardMessage("Atleta non trovato.", "error");
        return;
    }

    editingAthleteId = athlete.id;

    document.getElementById("athleteFirstName").value = athlete.first_name || "";
    document.getElementById("athleteLastName").value = athlete.last_name || "";
    document.getElementById("athleteBirthDate").value = normalizeDateInput(athlete.birth_date);
    document.getElementById("athleteGroup").value = athlete.group_name || "";
    document.getElementById("athletePhone").value = athlete.phone || "";
    document.getElementById("athleteEmail").value = athlete.email || "";
    document.getElementById("parentName").value = athlete.parent_name_1 || "";
    document.getElementById("parentPhone").value = athlete.parent_phone_1 || "";
    document.getElementById("parentEmail").value = athlete.parent_email_1 || "";
    document.getElementById("athleteNotes").value = athlete.notes || "";

    const submitBtn = document.querySelector("#addAthleteForm button[type='submit']");
    if(submitBtn){
        submitBtn.textContent = "Aggiorna atleta";
    }

    document.getElementById("addAthleteSection")?.scrollIntoView({ behavior:"smooth" });
    setDashboardMessage("Modifica atleta attiva. Aggiorna i campi e salva.", "info");
}

function resetAthleteForm(){
    editingAthleteId = null;

    const form = document.getElementById("addAthleteForm");
    if(form){
        form.reset();
    }

    const submitBtn = document.querySelector("#addAthleteForm button[type='submit']");
    if(submitBtn){
        submitBtn.textContent = "Salva atleta";
    }
}

async function handleAddAthlete(event){
    event.preventDefault();

    if(!requireVerifiedEmail("l'inserimento degli atleti")){
        return;
    }

    const payload = {
        first_name: document.getElementById("athleteFirstName").value.trim(),
        last_name: document.getElementById("athleteLastName").value.trim(),
        birth_date: document.getElementById("athleteBirthDate").value,
        group_name: document.getElementById("athleteGroup").value.trim(),
        phone: document.getElementById("athletePhone").value.trim() || null,
        email: document.getElementById("athleteEmail").value.trim() || null,
        parent_name_1: document.getElementById("parentName").value.trim() || null,
        parent_phone_1: document.getElementById("parentPhone").value.trim() || null,
        parent_email_1: document.getElementById("parentEmail").value.trim() || null,
        parent_name_2: null,
        parent_phone_2: null,
        parent_email_2: null,
        notes: document.getElementById("athleteNotes").value.trim() || null
    };

    setDashboardMessage(editingAthleteId ? "Aggiornamento atleta..." : "Salvataggio atleta...", "info");

    try{
        if(editingAthleteId){
            await apiRequest(`/athletes/${editingAthleteId}`, {
                method: "PATCH",
                body: JSON.stringify(payload)
            });

            resetAthleteForm();
            await refreshAll();
            setDashboardMessage("Atleta aggiornato correttamente.", "success");
        }else{
            await apiRequest("/athletes/", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            resetAthleteForm();
            await refreshAll();
            setDashboardMessage("Atleta inserito correttamente.", "success");
        }
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function deleteAthlete(athleteId){
    if(!requireVerifiedEmail("l'eliminazione degli atleti")){
        return;
    }

    if(!confirm("Vuoi eliminare questo atleta? Se ha pagamenti o certificati collegati, il backend bloccherà l'eliminazione.")){
        return;
    }

    setDashboardMessage("Eliminazione atleta...", "info");

    try{
        await apiRequest(`/athletes/${athleteId}`, {
            method: "DELETE"
        });

        if(openedAthleteId === athleteId){
            closeAthleteDetail();
        }

        await refreshAll();
        setDashboardMessage("Atleta eliminato.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

/* =========================
   Pagamenti
========================= */

function fillPaymentForm(paymentId){
    const payment = cachedPayments.find(item => Number(item.id) === Number(paymentId));

    if(!payment){
        setDashboardMessage("Pagamento non trovato.", "error");
        return;
    }

    editingPaymentId = payment.id;
    resetCertificateForm(false);

    document.getElementById("paymentAthleteId").value = String(payment.athlete_id || "");
    document.getElementById("paymentAmountDue").value = payment.amount_due ?? "";
    document.getElementById("paymentAmountPaid").value = payment.amount_paid ?? 0;
    document.getElementById("paymentDueDate").value = normalizeDateInput(payment.due_date);
    document.getElementById("paymentStatus").value = payment.status || "pending";
    document.getElementById("paymentMethod").value = payment.method || "";
    document.getElementById("paymentNotes").value = payment.notes || "";

    setText("paymentSubmitBtn", "Aggiorna pagamento");
    document.getElementById("cancelPaymentEditBtn")?.classList.remove("hidden");

    document.getElementById("paymentsSection")?.scrollIntoView({ behavior:"smooth" });
    setDashboardMessage("Modifica pagamento attiva. Aggiorna i campi e salva.", "info");
}

function resetPaymentForm(clearForm = true){
    editingPaymentId = null;

    const form = document.getElementById("addPaymentForm");
    if(form && clearForm){
        form.reset();
    }

    setText("paymentSubmitBtn", "Salva pagamento");
    document.getElementById("cancelPaymentEditBtn")?.classList.add("hidden");
}

async function handleAddPayment(event){
    event.preventDefault();

    if(!requireVerifiedEmail("la gestione dei pagamenti")){
        return;
    }

    const payload = {
        athlete_id: Number(document.getElementById("paymentAthleteId").value),
        amount_due: Number(document.getElementById("paymentAmountDue").value),
        amount_paid: Number(document.getElementById("paymentAmountPaid").value || 0),
        due_date: document.getElementById("paymentDueDate").value,
        status: document.getElementById("paymentStatus").value,
        method: document.getElementById("paymentMethod").value.trim() || null,
        notes: document.getElementById("paymentNotes").value.trim() || null
    };

    if(!payload.athlete_id){
        setDashboardMessage("Seleziona un atleta per il pagamento.", "error");
        return;
    }

    setDashboardMessage(editingPaymentId ? "Aggiornamento pagamento..." : "Salvataggio pagamento...", "info");

    try{
        if(editingPaymentId){
            await apiRequest(`/payments/${editingPaymentId}`, {
                method: "PATCH",
                body: JSON.stringify(payload)
            });

            resetPaymentForm();
            await refreshAll();
            setDashboardMessage("Pagamento aggiornato correttamente.", "success");
        }else{
            await apiRequest("/payments/", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            resetPaymentForm();
            await refreshAll();
            setDashboardMessage("Pagamento inserito correttamente.", "success");
        }
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function markPaymentPaid(paymentId){
    if(!requireVerifiedEmail("la gestione dei pagamenti")){
        return;
    }

    if(!confirm("Vuoi segnare questo pagamento come pagato?")) return;

    setDashboardMessage("Aggiornamento pagamento...", "info");

    try{
        await apiRequest(`/payments/${paymentId}/mark-paid`, {
            method: "PATCH"
        });

        if(editingPaymentId === paymentId){
            resetPaymentForm();
        }

        await refreshAll();
        setDashboardMessage("Pagamento segnato come pagato.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function deletePayment(paymentId){
    if(!requireVerifiedEmail("l'eliminazione dei pagamenti")){
        return;
    }

    if(!confirm("Vuoi eliminare questo pagamento?")) return;

    setDashboardMessage("Eliminazione pagamento...", "info");

    try{
        await apiRequest(`/payments/${paymentId}`, {
            method: "DELETE"
        });

        if(editingPaymentId === paymentId){
            resetPaymentForm();
        }

        await refreshAll();
        setDashboardMessage("Pagamento eliminato.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

/* =========================
   Certificati
========================= */

function fillCertificateForm(certificateId){
    const cert = cachedCertificates.find(item => Number(item.id) === Number(certificateId));

    if(!cert){
        setDashboardMessage("Certificato non trovato.", "error");
        return;
    }

    editingCertificateId = cert.id;
    resetPaymentForm(false);

    document.getElementById("certificateAthleteId").value = String(cert.athlete_id || "");
    document.getElementById("certificateType").value = cert.type || "Certificato medico sportivo";
    document.getElementById("certificateIssueDate").value = normalizeDateInput(cert.issue_date);
    document.getElementById("certificateExpiryDate").value = normalizeDateInput(cert.expiry_date);
    document.getElementById("certificateStatus").value = cert.status || "valid";

    setText("certificateSubmitBtn", "Aggiorna certificato");
    document.getElementById("cancelCertificateEditBtn")?.classList.remove("hidden");

    document.getElementById("certificatesSection")?.scrollIntoView({ behavior:"smooth" });
    setDashboardMessage("Modifica certificato attiva. Aggiorna i campi e salva.", "info");
}

function resetCertificateForm(clearForm = true){
    editingCertificateId = null;

    const form = document.getElementById("addCertificateForm");
    if(form && clearForm){
        form.reset();
    }

    const certificateType = document.getElementById("certificateType");
    if(certificateType && clearForm){
        certificateType.value = "Certificato medico sportivo";
    }

    setText("certificateSubmitBtn", "Salva certificato");
    document.getElementById("cancelCertificateEditBtn")?.classList.add("hidden");
}

async function handleAddCertificate(event){
    event.preventDefault();

    if(!requireVerifiedEmail("la gestione dei certificati")){
        return;
    }

    const payload = {
        athlete_id: Number(document.getElementById("certificateAthleteId").value),
        type: document.getElementById("certificateType").value.trim(),
        issue_date: document.getElementById("certificateIssueDate").value,
        expiry_date: document.getElementById("certificateExpiryDate").value,
        status: document.getElementById("certificateStatus").value,
        file_path: null
    };

    if(!payload.athlete_id){
        setDashboardMessage("Seleziona un atleta per il certificato.", "error");
        return;
    }

    setDashboardMessage(editingCertificateId ? "Aggiornamento certificato..." : "Salvataggio certificato...", "info");

    try{
        if(editingCertificateId){
            await apiRequest(`/certificates/${editingCertificateId}`, {
                method: "PATCH",
                body: JSON.stringify(payload)
            });

            resetCertificateForm();
            await refreshAll();
            setDashboardMessage("Certificato aggiornato correttamente.", "success");
        }else{
            await apiRequest("/certificates/", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            resetCertificateForm();
            await refreshAll();
            setDashboardMessage("Certificato inserito correttamente.", "success");
        }
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function markCertificateValid(certificateId){
    if(!requireVerifiedEmail("la gestione dei certificati")){
        return;
    }

    if(!confirm("Vuoi segnare questo certificato come valido?")) return;

    setDashboardMessage("Aggiornamento certificato...", "info");

    try{
        await apiRequest(`/certificates/${certificateId}/mark-valid`, {
            method: "PATCH"
        });

        if(editingCertificateId === certificateId){
            resetCertificateForm();
        }

        await refreshAll();
        setDashboardMessage("Certificato segnato come valido.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

async function deleteCertificate(certificateId){
    if(!requireVerifiedEmail("l'eliminazione dei certificati")){
        return;
    }

    if(!confirm("Vuoi eliminare questo certificato?")) return;

    setDashboardMessage("Eliminazione certificato...", "info");

    try{
        await apiRequest(`/certificates/${certificateId}`, {
            method: "DELETE"
        });

        if(editingCertificateId === certificateId){
            resetCertificateForm();
        }

        await refreshAll();
        setDashboardMessage("Certificato eliminato.", "success");
    }catch(error){
        setDashboardMessage(error.message, "error");
    }
}

/* =========================
   Scheda atleta
========================= */

function openAthleteDetail(athleteId, scroll = true){
    const athlete = cachedAthletes.find(item => Number(item.id) === Number(athleteId));

    if(!athlete){
        setDashboardMessage("Atleta non trovato.", "error");
        return;
    }

    openedAthleteId = athlete.id;

    const section = document.getElementById("athleteDetailSection");
    if(section){
        section.classList.remove("hidden");
    }

    const athletePayments = cachedPayments.filter(item => Number(item.athlete_id) === Number(athlete.id));
    const athleteCertificates = cachedCertificates.filter(item => Number(item.athlete_id) === Number(athlete.id));

    const totalResiduo = athletePayments.reduce((sum, payment) => {
        return sum + Math.max(0, Number(payment.amount_due || 0) - Number(payment.amount_paid || 0));
    }, 0);

    const certStatus = getBestCertificateStatus(athleteCertificates);

    setText("detailAthleteName", `${athlete.first_name} ${athlete.last_name}`);
    setText("detailAthleteGroup", athlete.group_name || "Senza gruppo");
    setText("detailAthleteBirth", formatDate(athlete.birth_date));
    setText("detailAthleteContact", athlete.parent_name_1 || athlete.email || athlete.phone || "Non indicato");
    setText("detailAthleteResiduo", formatEuro(totalResiduo));
    setText("detailAthleteCertificate", certStatus);

    renderDetailPayments(athletePayments);
    renderDetailCertificates(athleteCertificates);

    if(scroll){
        section?.scrollIntoView({ behavior:"smooth" });
    }
}

function quickCreatePaymentForOpenedAthlete(){
    if(!requireVerifiedEmail("il pagamento rapido")){
        return;
    }

    if(!openedAthleteId){
        setDashboardMessage("Apri prima una scheda atleta.", "error");
        return;
    }

    resetPaymentForm();

    const select = document.getElementById("paymentAthleteId");
    if(select){
        select.value = String(openedAthleteId);
    }

    const amountPaid = document.getElementById("paymentAmountPaid");
    const status = document.getElementById("paymentStatus");

    if(amountPaid && !amountPaid.value){
        amountPaid.value = "0";
    }

    if(status){
        status.value = "pending";
    }

    document.getElementById("paymentsSection")?.scrollIntoView({ behavior:"smooth" });
    setDashboardMessage("Pagamento rapido pronto per l'atleta selezionato.", "info");
}

function quickCreateCertificateForOpenedAthlete(){
    if(!requireVerifiedEmail("il certificato rapido")){
        return;
    }

    if(!openedAthleteId){
        setDashboardMessage("Apri prima una scheda atleta.", "error");
        return;
    }

    resetCertificateForm();

    const select = document.getElementById("certificateAthleteId");
    if(select){
        select.value = String(openedAthleteId);
    }

    const type = document.getElementById("certificateType");
    const status = document.getElementById("certificateStatus");

    if(type && !type.value){
        type.value = "Certificato medico sportivo";
    }

    if(status){
        status.value = "valid";
    }

    document.getElementById("certificatesSection")?.scrollIntoView({ behavior:"smooth" });
    setDashboardMessage("Certificato rapido pronto per l'atleta selezionato.", "info");
}

function closeAthleteDetail(){
    openedAthleteId = null;

    const section = document.getElementById("athleteDetailSection");
    if(section){
        section.classList.add("hidden");
    }
}

function renderDetailPayments(payments){
    const list = document.getElementById("detailPaymentsList");
    if(!list) return;

    if(!payments.length){
        list.innerHTML = `<div class="empty">Nessun pagamento collegato.</div>`;
        return;
    }

    list.innerHTML = payments.map(payment => {
        const residuo = Number(payment.amount_due || 0) - Number(payment.amount_paid || 0);
        const isPaid = residuo <= 0 || payment.status === "paid";

        return `
            <article class="mini-record">
                <strong>${isPaid ? "Pagato" : "Residuo " + formatEuro(residuo)}</strong>
                <span>Dovuto: ${formatEuro(payment.amount_due || 0)} · Pagato: ${formatEuro(payment.amount_paid || 0)}</span>
                <small>Scadenza: ${formatDate(payment.due_date)}</small>
            </article>
        `;
    }).join("");
}

function renderDetailCertificates(certificates){
    const list = document.getElementById("detailCertificatesList");
    if(!list) return;

    if(!certificates.length){
        list.innerHTML = `<div class="empty">Nessun certificato collegato.</div>`;
        return;
    }

    list.innerHTML = certificates.map(cert => {
        const status = getCertificateDisplayStatus(cert);

        return `
            <article class="mini-record">
                <strong class="${status.className}">${status.label}</strong>
                <span>${escapeHtml(cert.type)}</span>
                <small>Scadenza: ${formatDate(cert.expiry_date)}</small>
            </article>
        `;
    }).join("");
}

/* =========================
   WhatsApp V1.1 - Messaggi professionali
========================= */

function normalizeItalianPhone(phone){
    let raw = String(phone || "").trim();
    if(!raw) return "";

    raw = raw.replace(/[^0-9+]/g, "");

    if(raw.startsWith("+")) return raw.substring(1);
    if(raw.startsWith("00")) return raw.substring(2);
    if(raw.startsWith("39")) return raw;

    return `39${raw}`;
}

function getClubDisplayName(){
    return cachedClub?.name || "la società";
}

function openWhatsApp(phone, message, meta = {}){
    const cleanPhone = normalizeItalianPhone(phone);

    if(!cleanPhone){
        setDashboardMessage("Numero WhatsApp non disponibile.", "error");
        return;
    }

    const historyEntry = {
        type: meta.type || "WhatsApp",
        recipient: meta.recipient || meta.parentName || "Contatto",
        phone: cleanPhone,
        athlete: meta.athlete || "",
        message: message
    };

    saveCommunicationHistory(historyEntry);

    const url = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;
    const openedWindow = window.open(url, "_blank", "noopener,noreferrer");

    if(!openedWindow){
        setDashboardMessage("Storico aggiornato. Se WhatsApp non si apre, controlla il blocco popup del browser.", "info");
        return;
    }

    setDashboardMessage("WhatsApp aperto con messaggio precompilato e storico aggiornato.", "success");
}

function openWhatsAppParentRequest(requestId, type = "generic"){
    const request = cachedParentRequests.find(item => Number(item.id) === Number(requestId));

    if(!request){
        setDashboardMessage("Richiesta non trovata.", "error");
        return;
    }

    const athleteName = `${request.athlete_first_name || ""} ${request.athlete_last_name || ""}`.trim() || "l'atleta";
    const parentName = request.parent_name || "Genitore";
    const clubName = getClubDisplayName();

    let message =
`Ciao ${parentName},
ti contattiamo dalla segreteria di ${clubName} in merito alla richiesta di iscrizione di ${athleteName}.

Abbiamo ricevuto la richiesta e la stiamo verificando.

Ti aggiorneremo appena la pratica sarà completata.

Per qualsiasi informazione puoi rispondere direttamente a questo messaggio.

Grazie,
Segreteria ${clubName}`;

    if(type === "confirm"){
        message =
`Ciao ${parentName},
ti confermiamo che la richiesta di iscrizione di ${athleteName} è stata ricevuta correttamente.

La segreteria verificherà i dati inseriti, il certificato medico e l'eventuale ricevuta di pagamento.

Ti aggiorneremo appena la pratica sarà completata.

Grazie,
Segreteria ${clubName}`;
    }

    openWhatsApp(request.parent_phone, message, { type: type === "confirm" ? "Conferma iscrizione" : "Richiesta iscrizione", recipient: parentName || "Genitore", athlete: athleteName });
}

function openWhatsAppAthlete(athleteId, type = "generic"){
    const athlete = cachedAthletes.find(item => Number(item.id) === Number(athleteId));

    if(!athlete){
        setDashboardMessage("Atleta non trovato.", "error");
        return;
    }

    const athleteName = `${athlete.first_name || ""} ${athlete.last_name || ""}`.trim() || "l'atleta";
    const parentName = athlete.parent_name_1 || "Genitore";
    const phone = athlete.parent_phone_1 || athlete.phone;
    const clubName = getClubDisplayName();

    const message =
`Ciao ${parentName},
ti contattiamo dalla segreteria di ${clubName} per una comunicazione relativa a ${athleteName}.

Per qualsiasi informazione puoi rispondere direttamente a questo messaggio.

Grazie,
Segreteria ${clubName}`;

    openWhatsApp(phone, message, { type: "Comunicazione atleta", recipient: parentName || "Genitore", athlete: athleteName });
}

function openWhatsAppPayment(paymentId){
    const payment = cachedPayments.find(item => Number(item.id) === Number(paymentId));

    if(!payment){
        setDashboardMessage("Pagamento non trovato.", "error");
        return;
    }

    const athlete = getAthleteById(payment.athlete_id);
    const athleteName = athlete ? `${athlete.first_name || ""} ${athlete.last_name || ""}`.trim() : findAthlete(payment.athlete_id);
    const parentName = athlete?.parent_name_1 || "Genitore";
    const phone = athlete?.parent_phone_1 || athlete?.phone;
    const residuo = Math.max(0, Number(payment.amount_due || 0) - Number(payment.amount_paid || 0));
    const clubName = getClubDisplayName();

    const message =
`Ciao ${parentName},
ti ricordiamo che risulta ancora aperto un pagamento relativo a ${athleteName}.

Importo residuo: ${formatEuro(residuo)}
Scadenza: ${formatDate(payment.due_date)}

Per qualsiasi dubbio puoi rispondere direttamente a questo messaggio.

Grazie,
Segreteria ${clubName}`;

    openWhatsApp(phone, message, { type: "Sollecito quota", recipient: parentName || "Genitore", athlete: athleteName });
}

function openWhatsAppCertificate(certificateId){
    const cert = cachedCertificates.find(item => Number(item.id) === Number(certificateId));

    if(!cert){
        setDashboardMessage("Certificato non trovato.", "error");
        return;
    }

    const athlete = getAthleteById(cert.athlete_id);
    const athleteName = athlete ? `${athlete.first_name || ""} ${athlete.last_name || ""}`.trim() : findAthlete(cert.athlete_id);
    const parentName = athlete?.parent_name_1 || "Genitore";
    const phone = athlete?.parent_phone_1 || athlete?.phone;
    const clubName = getClubDisplayName();
    const status = getCertificateDisplayStatus(cert);

    const message =
`Ciao ${parentName},
ti ricordiamo che il certificato medico di ${athleteName} risulta ${String(status.label || "").toLowerCase()}.

Scadenza certificato: ${formatDate(cert.expiry_date)}

Ti chiediamo gentilmente di consegnare o caricare il nuovo certificato appena disponibile.

Grazie,
Segreteria ${clubName}`;

    openWhatsApp(phone, message, { type: "Promemoria certificato", recipient: parentName || "Genitore", athlete: athleteName });
}



/* =========================
   Comunicazioni rapide V1.2
========================= */

function sendQuickRegistrationLinkWhatsApp(){
    const phone = document.getElementById("quickRegistrationPhone")?.value || "";
    const parentName = document.getElementById("quickRegistrationParentName")?.value.trim() || "";
    const clubName = getClubDisplayName();
    const link = getRegistrationLinkValue();

    if(!link){
        setDashboardMessage("Link iscrizione non disponibile. Controlla il codice società.", "error");
        return;
    }

    const greeting = parentName ? `Ciao ${parentName},` : "Ciao,";
    const message =
`${greeting}
ti inviamo il link per compilare la richiesta di iscrizione atleta per ${clubName}.

${link}

Una volta inviato il modulo, la segreteria controllerà i dati e ti aggiornerà appena possibile.

Grazie,
Segreteria ${clubName}`;

    openWhatsApp(phone, message, { type: "Link iscrizione", recipient: parentName || "Genitore" });
}

function sendQuickDocumentsWhatsApp(){
    const phone = document.getElementById("quickDocumentsPhone")?.value || "";
    const athleteName = document.getElementById("quickDocumentsAthleteName")?.value.trim() || "l'atleta";
    const clubName = getClubDisplayName();

    const message =
`Ciao,
ti contattiamo dalla segreteria di ${clubName} per completare la pratica di ${athleteName}.

Ti chiediamo gentilmente di inviarci i documenti mancanti, come certificato medico e/o ricevuta di pagamento, appena disponibili.

Per qualsiasi dubbio puoi rispondere direttamente a questo messaggio.

Grazie,
Segreteria ${clubName}`;

    openWhatsApp(phone, message, { type: "Documenti mancanti", recipient: "Genitore", athlete: athleteName });
}

function sendQuickCustomWhatsApp(){
    const phone = document.getElementById("quickCustomPhone")?.value || "";
    const customMessage = document.getElementById("quickCustomMessage")?.value.trim() || "";
    const clubName = getClubDisplayName();

    if(!customMessage){
        setDashboardMessage("Scrivi prima il messaggio da inviare.", "error");
        return;
    }

    const message =
`${customMessage}

Segreteria ${clubName}`;

    openWhatsApp(phone, message, { type: "Comunicazione generale", recipient: "Contatto" });
}

/* =========================
   Utility stato e filtri
========================= */

function getAthleteAdminStatus(athlete){
    const payments = cachedPayments.filter(item => Number(item.athlete_id) === Number(athlete.id));
    const certificates = cachedCertificates.filter(item => Number(item.athlete_id) === Number(athlete.id));

    const hasOpenPayment = payments.some(payment => {
        const residuo = Number(payment.amount_due || 0) - Number(payment.amount_paid || 0);
        return residuo > 0 && payment.status !== "paid";
    });

    const certStatuses = certificates.map(cert => getCertificateDisplayStatus(cert));

    if(certStatuses.some(item => item.label === "Scaduto")){
        return { key:"certificate_expired", label:"Certificato scaduto", className:"status-certificate-expired" };
    }

    if(certStatuses.some(item => item.label === "In scadenza")){
        return { key:"certificate_expiring", label:"Certificato in scadenza", className:"status-certificate-expiring" };
    }

    if(hasOpenPayment){
        return { key:"payment_open", label:"Quota aperta", className:"status-payment-open" };
    }

    return { key:"ok", label:"OK", className:"status-ok" };
}

function getBestCertificateStatus(certificates){
    if(!certificates.length){
        return "Nessun certificato";
    }

    const statuses = certificates.map(cert => getCertificateDisplayStatus(cert));

    if(statuses.some(item => item.label === "Scaduto")){
        return "Scaduto";
    }

    if(statuses.some(item => item.label === "In scadenza")){
        return "In scadenza";
    }

    if(statuses.some(item => item.label === "Valido")){
        return "Valido";
    }

    return "Non indicato";
}

function getAthleteById(athleteId){
    return cachedAthletes.find(item => Number(item.id) === Number(athleteId)) || null;
}

function getFilteredPayments(){
    const search = (document.getElementById("paymentSearchInput")?.value || "").trim().toLowerCase();
    const group = document.getElementById("paymentGroupFilter")?.value || "";
    const statusFilter = document.getElementById("paymentStatusFilter")?.value || "";

    return cachedPayments.filter(payment => {
        const athlete = getAthleteById(payment.athlete_id);
        const paymentState = getPaymentStatusKey(payment);

        const haystack = [
            athlete?.first_name,
            athlete?.last_name,
            athlete?.group_name,
            payment.method,
            payment.notes,
            payment.status
        ].join(" ").toLowerCase();

        return (!search || haystack.includes(search)) &&
               (!group || ((athlete?.group_name || "Senza gruppo") === group)) &&
               (!statusFilter || paymentState === statusFilter);
    });
}

function getFilteredCertificates(){
    const search = (document.getElementById("certificateSearchInput")?.value || "").trim().toLowerCase();
    const group = document.getElementById("certificateGroupFilter")?.value || "";
    const statusFilter = document.getElementById("certificateStatusFilter")?.value || "";

    return cachedCertificates.filter(cert => {
        const athlete = getAthleteById(cert.athlete_id);
        const status = getCertificateStatusKey(cert);

        const haystack = [
            athlete?.first_name,
            athlete?.last_name,
            athlete?.group_name,
            cert.type,
            cert.status
        ].join(" ").toLowerCase();

        return (!search || haystack.includes(search)) &&
               (!group || ((athlete?.group_name || "Senza gruppo") === group)) &&
               (!statusFilter || status === statusFilter);
    });
}

function getPaymentStatusKey(payment){
    const residuo = Number(payment.amount_due || 0) - Number(payment.amount_paid || 0);

    if(residuo <= 0 || payment.status === "paid"){
        return "paid";
    }

    const today = new Date();
    today.setHours(0,0,0,0);

    const due = payment.due_date ? new Date(payment.due_date) : null;
    if(due && !Number.isNaN(due.getTime())){
        due.setHours(0,0,0,0);

        if(due < today || payment.status === "overdue"){
            return "overdue";
        }
    }

    return "open";
}

function getCertificateStatusKey(cert){
    const status = getCertificateDisplayStatus(cert);

    if(status.label === "Valido") return "valid";
    if(status.label === "In scadenza") return "expiring";
    if(status.label === "Scaduto") return "expired";

    return "";
}

function findAthlete(athleteId){
    const athlete = cachedAthletes.find(item => Number(item.id) === Number(athleteId));

    if(!athlete){
        return `Atleta #${athleteId}`;
    }

    return `${athlete.first_name} ${athlete.last_name}`;
}

function getCertificateDisplayStatus(cert){
    const savedStatus = String(cert?.status || "").toLowerCase();

    if(savedStatus === "expired"){
        return { label:"Scaduto", className:"status-danger" };
    }

    if(savedStatus === "expiring"){
        return { label:"In scadenza", className:"status-warning" };
    }

    if(savedStatus === "valid"){
        return { label:"Valido", className:"status-success" };
    }

    return getCertificateStatus(cert?.expiry_date);
}

function getCertificateStatus(expiryDate){
    if(!expiryDate){
        return { label:"Non indicato", className:"status-muted" };
    }

    const today = new Date();
    today.setHours(0,0,0,0);

    const expiry = new Date(expiryDate);
    expiry.setHours(0,0,0,0);

    const diffDays = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));

    if(diffDays < 0){
        return { label:"Scaduto", className:"status-danger" };
    }

    if(diffDays <= 30){
        return { label:"In scadenza", className:"status-warning" };
    }

    return { label:"Valido", className:"status-success" };
}

/* =========================
   Export CSV
========================= */

function exportPaymentsCsv(){
    const rows = getFilteredPayments();

    if(!rows.length){
        setDashboardMessage("Nessun pagamento da esportare con i filtri attuali.", "error");
        return;
    }

    const csvRows = [[
        "Atleta",
        "Gruppo",
        "Dovuto",
        "Pagato",
        "Residuo",
        "Scadenza",
        "Stato",
        "Metodo",
        "Note"
    ]];

    rows.forEach(payment => {
        const athlete = getAthleteById(payment.athlete_id);
        const residuo = Math.max(0, Number(payment.amount_due || 0) - Number(payment.amount_paid || 0));
        const state = getPaymentStatusKey(payment);

        csvRows.push([
            athlete ? `${athlete.first_name} ${athlete.last_name}` : `Atleta #${payment.athlete_id}`,
            athlete?.group_name || "Senza gruppo",
            Number(payment.amount_due || 0).toFixed(2),
            Number(payment.amount_paid || 0).toFixed(2),
            residuo.toFixed(2),
            normalizeDateInput(payment.due_date) || "",
            state === "paid" ? "Pagato" : state === "overdue" ? "Scaduto" : "Aperto",
            payment.method || "",
            payment.notes || ""
        ]);
    });

    downloadCsv(csvRows, `clubiq_pagamenti_${getTodaySlug()}.csv`);
    setDashboardMessage("Export pagamenti CSV creato.", "success");
}

function exportCertificatesCsv(){
    const rows = getFilteredCertificates();

    if(!rows.length){
        setDashboardMessage("Nessun certificato da esportare con i filtri attuali.", "error");
        return;
    }

    const csvRows = [[
        "Atleta",
        "Gruppo",
        "Tipo",
        "Data rilascio",
        "Data scadenza",
        "Stato"
    ]];

    rows.forEach(cert => {
        const athlete = getAthleteById(cert.athlete_id);
        const status = getCertificateDisplayStatus(cert);

        csvRows.push([
            athlete ? `${athlete.first_name} ${athlete.last_name}` : `Atleta #${cert.athlete_id}`,
            athlete?.group_name || "Senza gruppo",
            cert.type || "",
            normalizeDateInput(cert.issue_date) || "",
            normalizeDateInput(cert.expiry_date) || "",
            status.label
        ]);
    });

    downloadCsv(csvRows, `clubiq_certificati_${getTodaySlug()}.csv`);
    setDashboardMessage("Export certificati CSV creato.", "success");
}

function downloadCsv(rows, filename){
    const csvContent = rows
        .map(row => row.map(escapeCsvCell).join(";"))
        .join("\n");

    const blob = new Blob(["\ufeff" + csvContent], {
        type: "text/csv;charset=utf-8;"
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function escapeCsvCell(value){
    const raw = String(value ?? "");
    const escaped = raw.replaceAll('"', '""');
    return `"${escaped}"`;
}

/* =========================
   Utility generali
========================= */


function getTodayChecksData(){
    const pendingRequests = cachedParentRequests.filter(item => item.status === "pending").length;
    const overduePayments = cachedPayments.filter(payment => getPaymentStatusKey(payment) === "overdue").length;
    const expiredCertificates = cachedCertificates.filter(cert => getCertificateStatusKey(cert) === "expired").length;
    const expiringCertificates = cachedCertificates.filter(cert => getCertificateStatusKey(cert) === "expiring").length;

    return {
        pendingRequests,
        overduePayments,
        expiredCertificates,
        expiringCertificates,
        totalChecks: pendingRequests + overduePayments + expiredCertificates + expiringCertificates
    };
}

function getTodayChecksTotal(){
    return getTodayChecksData().totalChecks;
}

function renderTodayChecks(){
    const {
        pendingRequests,
        overduePayments,
        expiredCertificates,
        expiringCertificates,
        totalChecks
    } = getTodayChecksData();

    setText("todayPendingRequests", pendingRequests);
    setText("todayOverduePayments", overduePayments);
    setText("todayExpiredCertificates", expiredCertificates);
    setText("todayExpiringCertificates", expiringCertificates);

    const summary = document.getElementById("todayChecksSummary");

    if(!summary){
        return;
    }

    if(totalChecks === 0){
        summary.textContent = "Tutto sotto controllo: nessuna urgenza operativa al momento.";
        summary.className = "today-checks-summary success";
        return;
    }

    const parts = [];

    if(pendingRequests > 0){
        parts.push(`${pendingRequests} richieste genitori in attesa`);
    }

    if(overduePayments > 0){
        parts.push(`${overduePayments} quote scadute`);
    }

    if(expiredCertificates > 0){
        parts.push(`${expiredCertificates} certificati scaduti`);
    }

    if(expiringCertificates > 0){
        parts.push(`${expiringCertificates} certificati in scadenza`);
    }

    summary.textContent = `Hai ${totalChecks} attività da controllare: ${parts.join(", ")}.`;
    summary.className = "today-checks-summary warning";
}

function getTodaySlug(){
    return new Date().toISOString().slice(0, 10);
}

function setDashboardMessage(message, type){
    const box = document.getElementById("dashboardMessage");
    if(!box) return;

    box.textContent = message;
    box.className = `message ${type}`;
}

function setText(id, value){
    const el = document.getElementById(id);
    if(el) el.textContent = value;
}

function formatEuro(value){
    return new Intl.NumberFormat("it-IT", {
        style: "currency",
        currency: "EUR"
    }).format(value);
}

function formatDate(value){
    if(!value) return "Non indicata";

    const date = new Date(value);
    if(Number.isNaN(date.getTime())) return value;

    return date.toLocaleDateString("it-IT");
}

function normalizeDateInput(value){
    if(!value) return "";

    const raw = String(value);

    if(/^\d{4}-\d{2}-\d{2}$/.test(raw)){
        return raw;
    }

    const date = new Date(raw);

    if(Number.isNaN(date.getTime())){
        return "";
    }

    return date.toISOString().slice(0, 10);
}

function escapeHtml(value){
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
/* =========================
   WhatsApp V1.1 - Messaggi professionali
========================= */

function normalizePhoneForWhatsApp(phone){
    let raw = String(phone || "").trim();

    if(!raw){
        return "";
    }

    raw = raw.replace(/[^\d+]/g, "");

    if(raw.startsWith("+")){
        raw = raw.substring(1);
    }

    if(raw.startsWith("00")){
        raw = raw.substring(2);
    }

    if(raw.startsWith("39")){
        return raw;
    }

    return `39${raw}`;
}

function getClubDisplayName(){
    return cachedClub?.name || "la società";
}

function getAthleteFullNameFromObject(item){
    const firstName = item?.athlete_first_name || item?.first_name || "";
    const lastName = item?.athlete_last_name || item?.last_name || "";

    return `${firstName} ${lastName}`.trim() || "l'atleta";
}

function buildWhatsAppUrl(phone, message){
    const cleanPhone = normalizePhoneForWhatsApp(phone);

    if(!cleanPhone){
        return "";
    }

    return `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;
}

function openWhatsAppMessage(phone, message){
    const url = buildWhatsAppUrl(phone, message);

    if(!url){
        setDashboardMessage("Numero WhatsApp non disponibile o non valido.", "error");
        return;
    }

    window.open(url, "_blank", "noopener,noreferrer");
}

function openParentRequestWhatsApp(requestId){
    const request = cachedParentRequests.find(item => Number(item.id) === Number(requestId));

    if(!request){
        setDashboardMessage("Richiesta non trovata.", "error");
        return;
    }

    const parentName = request.parent_name || "Genitore";
    const athleteName = getAthleteFullNameFromObject(request);
    const clubName = getClubDisplayName();

    const message =
`Ciao ${parentName},
ti contattiamo dalla segreteria di ${clubName} in merito alla richiesta di iscrizione di ${athleteName}.

Abbiamo ricevuto la richiesta e la stiamo verificando.

Ti aggiorneremo appena la pratica sarà completata.

Per qualsiasi informazione puoi rispondere direttamente a questo messaggio.

Grazie,
Segreteria ${clubName}`;

    openWhatsAppMessage(request.parent_phone, message);
}

function openParentRequestConfirmationWhatsApp(requestId){
    const request = cachedParentRequests.find(item => Number(item.id) === Number(requestId));

    if(!request){
        setDashboardMessage("Richiesta non trovata.", "error");
        return;
    }

    const parentName = request.parent_name || "Genitore";
    const athleteName = getAthleteFullNameFromObject(request);
    const clubName = getClubDisplayName();

    const message =
`Ciao ${parentName},
ti confermiamo che la richiesta di iscrizione di ${athleteName} è stata ricevuta correttamente.

La segreteria verificherà i dati inseriti, il certificato medico e l'eventuale ricevuta di pagamento.

Ti aggiorneremo appena la pratica sarà completata.

Grazie,
Segreteria ${clubName}`;

    openWhatsAppMessage(request.parent_phone, message);
}

function openAthleteWhatsApp(athleteId){
    const athlete = cachedAthletes.find(item => Number(item.id) === Number(athleteId));

    if(!athlete){
        setDashboardMessage("Atleta non trovato.", "error");
        return;
    }

    const parentName = athlete.parent_name_1 || "Genitore";
    const athleteName = getAthleteFullNameFromObject(athlete);
    const clubName = getClubDisplayName();

    const message =
`Ciao ${parentName},
ti contattiamo dalla segreteria di ${clubName} per una comunicazione relativa a ${athleteName}.

Per qualsiasi informazione puoi rispondere direttamente a questo messaggio.

Grazie,
Segreteria ${clubName}`;

    openWhatsAppMessage(athlete.parent_phone_1 || athlete.phone, message);
}

function openPaymentReminderWhatsApp(paymentId){
    const payment = cachedPayments.find(item => Number(item.id) === Number(paymentId));

    if(!payment){
        setDashboardMessage("Pagamento non trovato.", "error");
        return;
    }

    const athlete = cachedAthletes.find(item => Number(item.id) === Number(payment.athlete_id));

    if(!athlete){
        setDashboardMessage("Atleta collegato al pagamento non trovato.", "error");
        return;
    }

    const parentName = athlete.parent_name_1 || "Genitore";
    const athleteName = getAthleteFullNameFromObject(athlete);
    const clubName = getClubDisplayName();

    const amountDue = Number(payment.amount_due || 0);
    const amountPaid = Number(payment.amount_paid || 0);
    const residual = Math.max(0, amountDue - amountPaid);

    const message =
`Ciao ${parentName},
ti ricordiamo che risulta ancora aperto un pagamento relativo a ${athleteName}.

Importo residuo: ${formatEuro(residual)}
Scadenza: ${formatDate(payment.due_date)}

Per qualsiasi dubbio puoi rispondere direttamente a questo messaggio.

Grazie,
Segreteria ${clubName}`;

    openWhatsAppMessage(athlete.parent_phone_1 || athlete.phone, message);
}

function openCertificateReminderWhatsApp(certificateId){
    const cert = cachedCertificates.find(item => Number(item.id) === Number(certificateId));

    if(!cert){
        setDashboardMessage("Certificato non trovato.", "error");
        return;
    }

    const athlete = cachedAthletes.find(item => Number(item.id) === Number(cert.athlete_id));

    if(!athlete){
        setDashboardMessage("Atleta collegato al certificato non trovato.", "error");
        return;
    }

    const parentName = athlete.parent_name_1 || "Genitore";
    const athleteName = getAthleteFullNameFromObject(athlete);
    const clubName = getClubDisplayName();
    const status = getCertificateDisplayStatus(cert);

    const message =
`Ciao ${parentName},
ti ricordiamo che il certificato medico di ${athleteName} risulta ${String(status.label || "").toLowerCase()}.

Scadenza certificato: ${formatDate(cert.expiry_date)}

Ti chiediamo gentilmente di consegnare o caricare il nuovo certificato appena disponibile.

Grazie,
Segreteria ${clubName}`;

    openWhatsAppMessage(athlete.parent_phone_1 || athlete.phone, message);
}

/* =========================
   Storico comunicazioni WhatsApp V1.3
========================= */

const COMMUNICATION_HISTORY_KEY = "clubiq_communication_history_v1";

function getCommunicationHistory(){
    try{
        const raw = localStorage.getItem(COMMUNICATION_HISTORY_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        if(Array.isArray(parsed)){
            return parsed;
        }
    }catch(error){
        console.warn("Storico comunicazioni non leggibile da localStorage:", error);
    }

    return Array.isArray(window.__clubiqCommunicationHistoryFallback)
        ? window.__clubiqCommunicationHistoryFallback
        : [];
}

function saveCommunicationHistory(entry){
    const history = getCommunicationHistory();

    const nextEntry = {
        id: Date.now(),
        created_at: new Date().toISOString(),
        type: entry.type || "WhatsApp",
        recipient: entry.recipient || "Contatto",
        phone: entry.phone || "",
        athlete: entry.athlete || "",
        message: entry.message || ""
    };

    history.unshift(nextEntry);
    const compact = history.slice(0, 30);

    try{
        localStorage.setItem(COMMUNICATION_HISTORY_KEY, JSON.stringify(compact));
        window.__clubiqCommunicationHistoryFallback = compact;
    }catch(error){
        console.warn("Storico comunicazioni non salvato in localStorage:", error);
        window.__clubiqCommunicationHistoryFallback = compact;
        setDashboardMessage("WhatsApp aperto. Storico salvato solo in memoria perché il browser blocca localStorage.", "info");
    }

    renderCommunicationHistory();
}

function populateCommunicationHistoryTypeFilter(history){
    const select = document.getElementById("communicationHistoryTypeFilter");
    if(!select) return;

    const currentValue = select.value || "";
    const types = [...new Set((history || []).map(item => item.type || item.kind || item.title || "Comunicazione").filter(Boolean))]
        .sort((a, b) => String(a).localeCompare(String(b), "it"));

    select.innerHTML = `<option value="">Tutte</option>` + types.map(type => `
        <option value="${escapeHtml(type)}">${escapeHtml(type)}</option>
    `).join("");

    if(currentValue && types.includes(currentValue)){
        select.value = currentValue;
    }
}

function getFilteredCommunicationHistory(history){
    const search = (document.getElementById("communicationHistorySearchInput")?.value || "").trim().toLowerCase();
    const typeFilter = document.getElementById("communicationHistoryTypeFilter")?.value || "";

    return (history || []).filter(item => {
        const type = item.type || item.kind || item.title || "Comunicazione";
        const haystack = [
            item.date,
            item.created_at,
            item.timestamp,
            type,
            item.recipient,
            item.name,
            item.phone,
            item.athlete,
            item.athleteName,
            item.message,
            item.text
        ].join(" ").toLowerCase();

        return (!search || haystack.includes(search)) &&
               (!typeFilter || String(type) === String(typeFilter));
    });
}

function renderCommunicationHistory(){
    const list = document.getElementById("communicationHistoryList");
    if(!list) return;

    const history = getCommunicationHistory();
    populateCommunicationHistoryTypeFilter(history);

    const filtered = getFilteredCommunicationHistory(history);
    const summary = document.getElementById("communicationHistorySummary");

    if(summary){
        summary.textContent = `${filtered.length} comunicazioni visualizzate su ${history.length} totali`;
    }

    if(!history.length){
        list.innerHTML = `<div class="empty">Nessuna comunicazione registrata.</div>`;
        return;
    }

    if(!filtered.length){
        list.innerHTML = `<div class="empty">Nessuna comunicazione trovata con questi filtri.</div>`;
        return;
    }

    list.innerHTML = filtered.map(item => {
        const type = item.type || item.kind || item.title || "Comunicazione";
        const recipient = item.recipient || item.name || "Destinatario non indicato";
        const phone = item.phone || "Telefono non indicato";
        const athlete = item.athlete || item.athleteName || "";
        const message = item.message || item.text || "";
        const date = item.date || item.created_at || item.timestamp || item.createdAt || new Date().toISOString();

        return `
            <article class="data-card communication-history-card">
                <div>
                    <strong>${escapeHtml(type)}</strong>
                    <span>${escapeHtml(formatDateTime(date))} · ${escapeHtml(recipient)} · ${escapeHtml(phone)}</span>
                    ${athlete ? `<span>Atleta: ${escapeHtml(athlete)}</span>` : ""}
                    ${message ? `<small>${escapeHtml(message)}</small>` : ""}
                </div>
            </article>
        `;
    }).join("");
}

function exportCommunicationHistoryCsv(){
    const allHistory = getCommunicationHistory();
    const history = getFilteredCommunicationHistory(allHistory);

    if(!Array.isArray(history) || history.length === 0){
        setDashboardMessage("Nessuna comunicazione da esportare con i filtri attivi.", "error");
        return;
    }

    const csvRows = [[
        "Data",
        "Tipo",
        "Destinatario",
        "Telefono",
        "Atleta",
        "Messaggio"
    ]];

    history.forEach(item => {
        csvRows.push([
            formatDateTime(item.created_at || item.date || item.timestamp || item.createdAt),
            item.type_label || item.type || item.kind || item.title || "Comunicazione",
            item.recipient || item.name || "-",
            item.phone || "-",
            item.athlete || item.athleteName || "-",
            item.message || item.text || "-"
        ]);
    });

    downloadCsv(csvRows, `storico_comunicazioni_clubiq_${getTodaySlug()}.csv`);
    setDashboardMessage("Storico comunicazioni esportato in CSV.", "success");
}

function formatDateTime(value){
    if(!value){
        return "-";
    }

    const date = new Date(value);

    if(Number.isNaN(date.getTime())){
        return String(value);
    }

    return date.toLocaleString("it-IT", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}
function clearCommunicationHistory(){
    if(!confirm("Vuoi pulire lo storico comunicazioni WhatsApp da questo dispositivo?")){
        return;
    }

    try{
        localStorage.removeItem("clubiq_communication_history_v1");
        localStorage.removeItem("clubiq_whatsapp_history_v1");
        renderCommunicationHistory();
        setDashboardMessage("Storico comunicazioni pulito.", "success");
    }catch(error){
        setDashboardMessage("Impossibile pulire lo storico comunicazioni.", "error");
    }
}



/* =========================
   Report Segreteria PDF V1
========================= */

function generateSecretaryReportPdf(){
    try{
        const clubName = cachedClub?.name || "ClubIQ Segreteria";
        const today = new Date();
        const todayLabel = today.toLocaleString("it-IT", { day:"2-digit", month:"2-digit", year:"numeric", hour:"2-digit", minute:"2-digit" });
        const checks = getTodayChecksData();
        const history = getCommunicationHistory().slice(0, 8);
        const openPayments = cachedPayments.filter(payment => getPaymentStatusKey(payment) === "open").length;
        const paidPayments = cachedPayments.filter(payment => getPaymentStatusKey(payment) === "paid").length;
        const overduePayments = cachedPayments.filter(payment => getPaymentStatusKey(payment) === "overdue").length;
        const validCertificates = cachedCertificates.filter(cert => getCertificateStatusKey(cert) === "valid").length;
        const expiringCertificates = cachedCertificates.filter(cert => getCertificateStatusKey(cert) === "expiring").length;
        const expiredCertificates = cachedCertificates.filter(cert => getCertificateStatusKey(cert) === "expired").length;
        const totalResidual = cachedPayments.reduce((sum, payment) => sum + Math.max(0, Number(payment.amount_due || 0) - Number(payment.amount_paid || 0)), 0);

        const rows = history.length ? history.map(item => `
            <tr>
                <td>${escapeHtml(formatDateTime(item.created_at || item.date || item.timestamp))}</td>
                <td>${escapeHtml(item.type_label || item.type || "Comunicazione")}</td>
                <td>${escapeHtml(item.recipient || item.name || "-")}</td>
                <td>${escapeHtml(item.phone || "-")}</td>
            </tr>
        `).join("") : `<tr><td colspan="4">Nessuna comunicazione registrata su questo dispositivo.</td></tr>`;

        const html = `<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>Report Segreteria - ${escapeHtml(clubName)}</title>
<style>
body{font-family:Arial,sans-serif;color:#0f172a;margin:32px;background:#fff} .header{border-bottom:3px solid #2563eb;padding-bottom:16px;margin-bottom:22px}.eyebrow{color:#2563eb;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}h1{margin:6px 0;font-size:28px}h2{font-size:18px;margin:26px 0 12px}.muted{color:#64748b}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card{border:1px solid #dbe3ef;border-radius:14px;padding:14px;background:#f8fafc}.card span{display:block;color:#64748b;font-size:11px;font-weight:800;text-transform:uppercase}.card strong{display:block;font-size:24px;margin-top:8px}.danger strong{color:#dc2626}.warning strong{color:#d97706}.success strong{color:#16a34a}table{width:100%;border-collapse:collapse;margin-top:10px}th,td{border:1px solid #dbe3ef;padding:9px;text-align:left;font-size:12px}th{background:#eff6ff;color:#1d4ed8}.footer{margin-top:30px;color:#64748b;font-size:11px;border-top:1px solid #dbe3ef;padding-top:12px}@media print{button{display:none}body{margin:18px}.grid{grid-template-columns:repeat(4,1fr)}}
</style>
</head>
<body>
<div class="header"><div class="eyebrow">ClubIQ Segreteria</div><h1>Report segreteria</h1><div class="muted">${escapeHtml(clubName)} · Generato il ${escapeHtml(todayLabel)}</div></div>
<h2>Riepilogo operativo</h2><div class="grid">
<div class="card"><span>Atleti totali</span><strong>${cachedAthletes.length}</strong></div>
<div class="card warning"><span>Richieste in attesa</span><strong>${checks.pendingRequests}</strong></div>
<div class="card danger"><span>Quote scadute</span><strong>${overduePayments}</strong></div>
<div class="card danger"><span>Certificati scaduti</span><strong>${expiredCertificates}</strong></div>
</div>
<h2>Pagamenti</h2><div class="grid"><div class="card"><span>Pagati</span><strong>${paidPayments}</strong></div><div class="card warning"><span>Aperti</span><strong>${openPayments}</strong></div><div class="card danger"><span>Scaduti</span><strong>${overduePayments}</strong></div><div class="card"><span>Residuo</span><strong>${formatEuro(totalResidual)}</strong></div></div>
<h2>Certificati</h2><div class="grid"><div class="card success"><span>Validi</span><strong>${validCertificates}</strong></div><div class="card warning"><span>In scadenza</span><strong>${expiringCertificates}</strong></div><div class="card danger"><span>Scaduti</span><strong>${expiredCertificates}</strong></div><div class="card"><span>Totali</span><strong>${cachedCertificates.length}</strong></div></div>
<h2>Ultime comunicazioni WhatsApp</h2><table><thead><tr><th>Data</th><th>Tipo</th><th>Destinatario</th><th>Telefono</th></tr></thead><tbody>${rows}</tbody></table>
<div class="footer">Report generato da ClubIQ. I dati WhatsApp sono salvati localmente sul dispositivo della segreteria.</div>
<script>window.onload=function(){setTimeout(function(){window.print()},300)}</script>
</body></html>`;
        const reportWindow = window.open("", "_blank", "noopener,noreferrer");
        if(!reportWindow){ setDashboardMessage("Popup bloccato: abilita le finestre popup per generare il PDF.", "error"); return; }
        reportWindow.document.open(); reportWindow.document.write(html); reportWindow.document.close();
        setDashboardMessage("Report segreteria aperto. Usa Salva come PDF dalla finestra di stampa.", "success");
    }catch(error){
        console.error(error);
        setDashboardMessage("Errore durante la generazione del report PDF.", "error");
    }
}
