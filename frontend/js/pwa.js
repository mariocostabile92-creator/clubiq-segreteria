/*
  ClubIQ Segreteria - PWA
  V1.4 Emergency Off
*/

window.addEventListener("load", async () => {
    if (!("serviceWorker" in navigator)) {
        return;
    }

    try {
        const registrations = await navigator.serviceWorker.getRegistrations();

        for (const registration of registrations) {
            await registration.unregister();
        }

        console.log("ClubIQ service worker disattivato temporaneamente");
    } catch (error) {
        console.warn("Errore disattivazione service worker:", error);
    }
});