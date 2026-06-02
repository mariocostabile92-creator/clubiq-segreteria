/*
  ClubIQ Segreteria - PWA Register
  V1.1
*/

let deferredInstallPrompt = null;

if("serviceWorker" in navigator){
    window.addEventListener("load", () => {
        navigator.serviceWorker
            .register("/service-worker.js")
            .then(() => console.log("ClubIQ PWA pronta"))
            .catch(error => console.warn("Service Worker non registrato:", error));
    });
}

window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault();
    deferredInstallPrompt = event;

    const installBtn = document.getElementById("installPwaBtn");
    if(installBtn){
        installBtn.classList.remove("hidden");
    }
});

async function installClubIQPWA(){
    if(!deferredInstallPrompt){
        alert("Installazione non disponibile in questo momento. Su mobile puoi usare 'Aggiungi a schermata Home'.");
        return;
    }

    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;

    deferredInstallPrompt = null;

    const installBtn = document.getElementById("installPwaBtn");
    if(installBtn){
        installBtn.classList.add("hidden");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const installBtn = document.getElementById("installPwaBtn");

    if(installBtn){
        installBtn.addEventListener("click", installClubIQPWA);
    }
});