/*
  ClubIQ Segreteria - PWA
  V1.5 Install Guide Safe
  Mantiene disattivata la cache aggressiva, ma lascia visibile la guida installazione.
*/

let clubiqDeferredInstallPrompt = null;

window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    clubiqDeferredInstallPrompt = event;
});

window.addEventListener("load", async () => {
    if (!("serviceWorker" in navigator)) {
        return;
    }

    try {
        const registrations = await navigator.serviceWorker.getRegistrations();

        for (const registration of registrations) {
            await registration.unregister();
        }

        console.log("ClubIQ service worker disattivato temporaneamente: installazione guidata attiva");
    } catch (error) {
        console.warn("Errore disattivazione service worker:", error);
    }
});

window.clubiqTryNativeInstall = async function(){
    if(!clubiqDeferredInstallPrompt){
        return false;
    }

    clubiqDeferredInstallPrompt.prompt();
    await clubiqDeferredInstallPrompt.userChoice;
    clubiqDeferredInstallPrompt = null;
    return true;
};
