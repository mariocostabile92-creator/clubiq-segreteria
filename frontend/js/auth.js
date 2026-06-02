/*
  ClubIQ Segreteria - Auth
  V1.2 Emergency Stable
*/

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    const showLoginBtn = document.getElementById("showLogin");
    const showSignupBtn = document.getElementById("showSignup");

    if(showLoginBtn){
        showLoginBtn.addEventListener("click", () => {
            showAuthPanel("login");
        });
    }

    if(showSignupBtn){
        showSignupBtn.addEventListener("click", () => {
            showAuthPanel("signup");
        });
    }

    if(loginForm){
        loginForm.addEventListener("submit", handleLogin);
    }

    if(signupForm){
        signupForm.addEventListener("submit", handleSignup);
    }

    showAuthPanel("login");
});

function showAuthPanel(type){
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    const showLoginBtn = document.getElementById("showLogin");
    const showSignupBtn = document.getElementById("showSignup");

    if(!loginForm || !signupForm) return;

    if(type === "login"){
        loginForm.classList.remove("hidden");
        signupForm.classList.add("hidden");

        if(showLoginBtn) showLoginBtn.classList.add("active");
        if(showSignupBtn) showSignupBtn.classList.remove("active");
    }else{
        signupForm.classList.remove("hidden");
        loginForm.classList.add("hidden");

        if(showSignupBtn) showSignupBtn.classList.add("active");
        if(showLoginBtn) showLoginBtn.classList.remove("active");
    }

    clearAuthMessage();
}

async function handleLogin(event){
    event.preventDefault();

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    if(!username || !password){
        setAuthMessage("Inserisci username e password.", "error");
        return;
    }

    setAuthMessage("Accesso in corso...", "info");

    try{
        const data = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });

        setToken(data.access_token);
        setAuthMessage("Login effettuato. Apro la dashboard...", "success");

        window.location.assign("/dashboard.html");
    }catch(error){
        setAuthMessage(error.message || "Credenziali non valide.", "error");
    }
}

async function handleSignup(event){
    event.preventDefault();

    const club_name = document.getElementById("signupClubName").value.trim();
    const username = document.getElementById("signupUsername").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value.trim();

    if(!club_name || !username || !email || !password){
        setAuthMessage("Compila tutti i campi per creare la società.", "error");
        return;
    }

    setAuthMessage("Creazione società in corso...", "info");

    try{
        const data = await apiRequest("/auth/signup", {
            method: "POST",
            body: JSON.stringify({
                club_name,
                username,
                email,
                password
            })
        });

        setToken(data.access_token);
        setAuthMessage("Società creata. Apro la dashboard...", "success");

        window.location.assign("/dashboard.html");
    }catch(error){
        setAuthMessage(error.message || "Errore durante la creazione della società.", "error");
    }
}

function setAuthMessage(message, type){
    const box = document.getElementById("authMessage");
    if(!box) return;

    box.textContent = message;
    box.className = `message ${type}`;
}

function clearAuthMessage(){
    const box = document.getElementById("authMessage");
    if(!box) return;

    box.textContent = "";
    box.className = "message hidden";
}