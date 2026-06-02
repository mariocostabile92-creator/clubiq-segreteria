/*
  ClubIQ Segreteria - Auth
  V1.0
*/

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    const showLoginBtn = document.getElementById("showLogin");
    const showSignupBtn = document.getElementById("showSignup");

    if(isLoggedIn() && window.location.pathname.endsWith("index.html")){
        window.location.href = "dashboard.html";
        return;
    }

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
});

function showAuthPanel(type){
    const loginPanel = document.getElementById("loginPanel");
    const signupPanel = document.getElementById("signupPanel");
    const showLoginBtn = document.getElementById("showLogin");
    const showSignupBtn = document.getElementById("showSignup");

    if(type === "login"){
        loginPanel.classList.remove("hidden");
        signupPanel.classList.add("hidden");
        showLoginBtn.classList.add("active");
        showSignupBtn.classList.remove("active");
    }else{
        signupPanel.classList.remove("hidden");
        loginPanel.classList.add("hidden");
        showSignupBtn.classList.add("active");
        showLoginBtn.classList.remove("active");
    }
}

async function handleLogin(event){
    event.preventDefault();

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    setAuthMessage("Accesso in corso...", "info");

    try{
        const data = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });

        setToken(data.access_token);
        setAuthMessage("Login effettuato. Reindirizzamento...", "success");

        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 500);
    }catch(error){
        setAuthMessage(error.message, "error");
    }
}

async function handleSignup(event){
    event.preventDefault();

    const club_name = document.getElementById("signupClubName").value.trim();
    const username = document.getElementById("signupUsername").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value.trim();

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
        setAuthMessage("Società creata. Reindirizzamento...", "success");

        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 500);
    }catch(error){
        setAuthMessage(error.message, "error");
    }
}

function setAuthMessage(message, type){
    const box = document.getElementById("authMessage");
    if(!box) return;

    box.textContent = message;
    box.className = `message ${type}`;
}