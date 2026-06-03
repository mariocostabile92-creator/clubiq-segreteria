/*
  ClubIQ Segreteria - PWA
  V1.5 Install Guide Safe
*/

let deferredClubIqInstallPrompt = null;

window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredClubIqInstallPrompt = event;
    const btn = document.getElementById("installPwaBtn");
    if(btn) btn.classList.remove("hidden");
});

window.addEventListener("load", async () => {
    if ("serviceWorker" in navigator) {
        try {
            const registrations = await navigator.serviceWorker.getRegistrations();
            for (const registration of registrations) {
                await registration.unregister();
            }
            console.log("ClubIQ service worker safe mode: cache disattivata");
        } catch (error) {
            console.warn("Errore gestione service worker:", error);
        }
    }

    bindClubIqInstallGuide();
});

function bindClubIqInstallGuide(){
    const buttons = document.querySelectorAll("#installPwaBtn, [data-open-pwa-guide]");
    buttons.forEach((btn) => {
        btn.classList.remove("hidden");
        btn.addEventListener("click", openClubIqInstallGuide);
    });
}

async function openClubIqInstallGuide(){
    if(deferredClubIqInstallPrompt){
        deferredClubIqInstallPrompt.prompt();
        await deferredClubIqInstallPrompt.userChoice;
        deferredClubIqInstallPrompt = null;
        return;
    }

    alert(
        "Installa ClubIQ come app:\n\n" +
        "iPhone/iPad:\n" +
        "1. Apri ClubIQ con Safari\n" +
        "2. Tocca Condividi\n" +
        "3. Tocca Aggiungi alla schermata Home\n\n" +
        "Android:\n" +
        "1. Apri il menu del browser\n" +
        "2. Tocca Installa app o Aggiungi a schermata Home"
    );
}
