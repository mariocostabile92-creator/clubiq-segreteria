/*
  ClubIQ Segreteria - Auth
  V2.3 Login Click Hard Fix + Cache Bust
*/

document.addEventListener("DOMContentLoaded", () => {
    bindAuthActions();
    handleAuthQueryParams();
});

function bindAuthActions(){
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    const showLoginBtn = document.getElementById("showLogin");
    const showSignupBtn = document.getElementById("showSignup");
    const showForgotPasswordBtn = document.getElementById("showForgotPasswordBtn");
    const forgotPasswordForm = document.getElementById("forgotPasswordForm");
    const resetPasswordForm = document.getElementById("resetPasswordForm");
    const backToLoginBtns = document.querySelectorAll("[data-auth-back-login]");

    if(showLoginBtn) showLoginBtn.addEventListener("click", () => showAuthPanel("login"));
    if(showSignupBtn) showSignupBtn.addEventListener("click", () => showAuthPanel("signup"));
    if(showForgotPasswordBtn) showForgotPasswordBtn.addEventListener("click", () => showAuthPanel("forgot"));
    backToLoginBtns.forEach(btn => btn.addEventListener("click", () => showAuthPanel("login")));

    if(loginForm){
        loginForm.addEventListener("submit", handleLogin);
        const loginButton = loginForm.querySelector('button[type="submit"]');
        if(loginButton){
            loginButton.addEventListener("click", (event) => {
                event.preventDefault();
                handleLogin({ preventDefault(){}, currentTarget: loginForm });
            });
        }
    }

    if(signupForm){
        signupForm.addEventListener("submit", handleSignup);
        const signupButton = signupForm.querySelector('button[type="submit"]');
        if(signupButton){
            signupButton.addEventListener("click", (event) => {
                event.preventDefault();
                handleSignup({ preventDefault(){}, currentTarget: signupForm });
            });
        }
    }

    if(forgotPasswordForm) forgotPasswordForm.addEventListener("submit", handleForgotPassword);
    if(resetPasswordForm) resetPasswordForm.addEventListener("submit", handleResetPassword);
    showAuthPanel("login");
}

async function handleAuthQueryParams(){
    const params = new URLSearchParams(window.location.search);
    const verifyToken = params.get("verify_token");
    const resetToken = params.get("reset_token");
    if(verifyToken){
        setAuthMessage("Verifica email in corso...", "info");
        try{
            const data = await apiRequest("/auth/verify-email", { method:"POST", body:JSON.stringify({ token: verifyToken }) });
            cleanAuthUrl(); showAuthPanel("login");
            setAuthMessage(data.message || "Email verificata. Ora puoi accedere.", "success");
        }catch(error){
            cleanAuthUrl(); showAuthPanel("login");
            setAuthMessage(error.message || "Link verifica email non valido o scaduto.", "error");
        }
        return;
    }
    if(resetToken){
        const tokenInput = document.getElementById("resetPasswordToken");
        if(tokenInput) tokenInput.value = resetToken;
        showAuthPanel("reset");
        setAuthMessage("Imposta la nuova password per completare il reset.", "info");
    }
}

function cleanAuthUrl(){ window.history.replaceState({}, document.title, window.location.pathname + "#accesso"); }

function showAuthPanel(type){
    const panels = { login:document.getElementById("loginForm"), signup:document.getElementById("signupForm"), forgot:document.getElementById("forgotPasswordForm"), reset:document.getElementById("resetPasswordForm") };
    Object.values(panels).forEach(panel => panel?.classList.add("hidden"));
    panels[type]?.classList.remove("hidden");
    document.getElementById("showLogin")?.classList.toggle("active", type === "login");
    document.getElementById("showSignup")?.classList.toggle("active", type === "signup");
    if(type !== "reset") clearAuthMessage();
}

async function handleLogin(event){
    event.preventDefault();
    const form = event.currentTarget || document.getElementById("loginForm");
    const submitBtn = form?.querySelector('button[type="submit"]');
    const username = document.getElementById("loginUsername")?.value.trim() || "";
    const password = document.getElementById("loginPassword")?.value.trim() || "";
    if(!username || !password){ setAuthMessage("Inserisci username/email e password.", "error"); return; }
    setButtonLoading(submitBtn, true, "Accesso...");
    setAuthMessage("Accesso in corso...", "info");
    try{
        const data = await apiRequest("/auth/login", { method:"POST", body:JSON.stringify({ username, password }) });
        if(!data?.access_token) throw new Error("Token di accesso non ricevuto dal server.");
        setToken(data.access_token);
        localStorage.setItem("clubiq_token", data.access_token);
        setAuthMessage("Login effettuato. Apro la dashboard...", "success");
        forceRedirectToDashboard();
    }catch(error){
        console.error("Errore login ClubIQ:", error);
        setAuthMessage(error.message || "Credenziali non valide.", "error");
        setButtonLoading(submitBtn, false, "Entra nella dashboard");
    }
}

async function handleSignup(event){
    event.preventDefault();
    const form = event.currentTarget || document.getElementById("signupForm");
    const submitBtn = form?.querySelector('button[type="submit"]');
    const club_name = document.getElementById("signupClubName")?.value.trim() || "";
    const username = document.getElementById("signupUsername")?.value.trim() || "";
    const email = document.getElementById("signupEmail")?.value.trim() || "";
    const password = document.getElementById("signupPassword")?.value.trim() || "";
    if(!club_name || !username || !email || !password){ setAuthMessage("Compila tutti i campi per creare la società.", "error"); return; }
    if(password.length < 8){ setAuthMessage("La password deve contenere almeno 8 caratteri.", "error"); return; }
    setButtonLoading(submitBtn, true, "Creazione...");
    setAuthMessage("Creazione società...", "info");
    try{
        const data = await apiRequest("/auth/signup", { method:"POST", body:JSON.stringify({ club_name, username, email, password }) });
        if(!data?.access_token) throw new Error("Token di accesso non ricevuto dal server.");
        setToken(data.access_token);
        localStorage.setItem("clubiq_token", data.access_token);
        setAuthMessage("Società creata. Apro la dashboard...", "success");
        forceRedirectToDashboard();
    }catch(error){
        console.error("Errore registrazione ClubIQ:", error);
        setAuthMessage(error.message || "Errore durante la creazione della società.", "error");
        setButtonLoading(submitBtn, false, "Crea società");
    }
}

function forceRedirectToDashboard(){
    const target = window.location.origin + "/dashboard.html?v=" + Date.now();
    window.location.href = target;
    setTimeout(() => { window.location.assign(target); }, 500);
    setTimeout(() => { window.location.replace(target); }, 1200);
}

function setButtonLoading(button, loading, text){ if(button){ button.disabled = loading; button.textContent = text; } }

async function handleForgotPassword(event){
    event.preventDefault();
    const email = document.getElementById("forgotPasswordEmail")?.value.trim() || "";
    if(!email){ setAuthMessage("Inserisci la tua email.", "error"); return; }
    setAuthMessage("Invio link reset password...", "info");
    try{ const data = await apiRequest("/auth/forgot-password", { method:"POST", body:JSON.stringify({ email }) }); setAuthMessage(data.message || "Controlla la tua email.", "success"); }
    catch(error){ setAuthMessage(error.message || "Errore durante l'invio del reset password.", "error"); }
}

async function handleResetPassword(event){
    event.preventDefault();
    const token = document.getElementById("resetPasswordToken")?.value.trim() || "";
    const new_password = document.getElementById("resetNewPassword")?.value.trim() || "";
    const confirmPassword = document.getElementById("resetConfirmPassword")?.value.trim() || "";
    if(!token || !new_password){ setAuthMessage("Link reset non valido o password mancante.", "error"); return; }
    if(new_password.length < 8){ setAuthMessage("La nuova password deve contenere almeno 8 caratteri.", "error"); return; }
    if(new_password !== confirmPassword){ setAuthMessage("Le password non coincidono.", "error"); return; }
    setAuthMessage("Aggiornamento password...", "info");
    try{ const data = await apiRequest("/auth/reset-password", { method:"POST", body:JSON.stringify({ token, new_password }) }); cleanAuthUrl(); showAuthPanel("login"); setAuthMessage(data.message || "Password aggiornata. Ora puoi accedere.", "success"); }
    catch(error){ setAuthMessage(error.message || "Errore durante il reset password.", "error"); }
}

function setAuthMessage(message, type){
    const box = document.getElementById("authMessage");
    if(!box){ alert(message); return; }
    box.textContent = message;
    box.className = `message ${type}`;
    box.classList.remove("hidden");
}

function clearAuthMessage(){
    const box = document.getElementById("authMessage");
    if(!box) return;
    box.textContent = "";
    box.className = "message hidden";
}
