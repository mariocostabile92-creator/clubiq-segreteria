/*
  ClubIQ Segreteria - Iscrizione Genitore Pubblica
  V1.4 Upload documenti Cloudinary
*/

document.addEventListener("DOMContentLoaded", () => {
    bindParentRequestActions();
    preloadClubCodeFromUrl();
});

function bindParentRequestActions(){
    const form = document.getElementById("parentRequestForm");
    const clearFormBtn = document.getElementById("clearFormBtn");

    if(form){
        form.addEventListener("submit", handleParentRequestSubmit);
    }

    if(clearFormBtn){
        clearFormBtn.addEventListener("click", clearParentRequestForm);
    }
}

function preloadClubCodeFromUrl(){
    const params = new URLSearchParams(window.location.search);
    const code = params.get("club") || params.get("club_code") || params.get("code");

    if(code){
        const input = document.getElementById("clubCode");
        if(input){
            input.value = code.toUpperCase();
        }
    }
}

async function handleParentRequestSubmit(event){
    event.preventDefault();

    const certificateFile = document.getElementById("certificateFile")?.files?.[0] || null;
    const paymentReceiptFile = document.getElementById("paymentReceiptFile")?.files?.[0] || null;

    if(!validateUploadFile(certificateFile) || !validateUploadFile(paymentReceiptFile)){
        return;
    }

    const payload = {
        club_code: document.getElementById("clubCode").value.trim().toUpperCase(),
        athlete_first_name: document.getElementById("athleteFirstName").value.trim(),
        athlete_last_name: document.getElementById("athleteLastName").value.trim(),
        athlete_birth_date: document.getElementById("athleteBirthDate").value,
        requested_group: document.getElementById("requestedGroup").value.trim() || null,
        parent_name: document.getElementById("parentName").value.trim(),
        parent_phone: document.getElementById("parentPhone").value.trim() || null,
        parent_email: document.getElementById("parentEmail").value.trim(),
        certificate_file_url: null,
        payment_receipt_url: null,
        notes: document.getElementById("requestNotes").value.trim() || null
    };

    if(!payload.club_code){
        setRequestMessage("Inserisci il codice società fornito dalla segreteria.", "error");
        return;
    }

    if(!payload.athlete_first_name || !payload.athlete_last_name || !payload.athlete_birth_date){
        setRequestMessage("Compila i dati obbligatori dell'atleta.", "error");
        return;
    }

    if(!payload.parent_name || !payload.parent_email){
        setRequestMessage("Compila nome ed email del genitore.", "error");
        return;
    }

    setSubmitLoading(true);

    try{
        if(certificateFile){
            setRequestMessage("Caricamento certificato medico...", "info");
            payload.certificate_file_url = await uploadParentDocument(certificateFile, "certificate");
        }

        if(paymentReceiptFile){
            setRequestMessage("Caricamento ricevuta pagamento...", "info");
            payload.payment_receipt_url = await uploadParentDocument(paymentReceiptFile, "receipt");
        }

        setRequestMessage("Invio richiesta in corso...", "info");

        await publicApiRequest("/public/parent-requests/", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        const usedCode = payload.club_code;
        clearParentRequestForm(false);

        const clubCodeInput = document.getElementById("clubCode");
        if(clubCodeInput){
            clubCodeInput.value = usedCode;
        }

        setRequestMessage("Richiesta inviata correttamente. La segreteria potrà verificarla e aprire i documenti caricati.", "success");
    }catch(error){
        setRequestMessage(error.message || "Errore durante l'invio della richiesta.", "error");
    }finally{
        setSubmitLoading(false);
    }
}

async function uploadParentDocument(file, documentType){
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/public/parent-requests/upload-document?document_type=${encodeURIComponent(documentType)}`, {
        method: "POST",
        body: formData
    });

    const data = await response.json().catch(() => null);

    if(!response.ok){
        throw new Error(data?.detail || "Errore durante il caricamento del documento.");
    }

    if(!data?.url){
        throw new Error("Documento caricato ma URL non disponibile.");
    }

    return data.url;
}

function validateUploadFile(file){
    if(!file){
        return true;
    }

    const allowedTypes = ["application/pdf", "image/jpeg", "image/png", "image/webp"];
    const maxSize = 8 * 1024 * 1024;

    if(!allowedTypes.includes(file.type)){
        setRequestMessage("Formato file non valido. Usa PDF, JPG, PNG o WEBP.", "error");
        return false;
    }

    if(file.size > maxSize){
        setRequestMessage("File troppo grande. Dimensione massima: 8 MB.", "error");
        return false;
    }

    return true;
}

async function publicApiRequest(path, options = {}){
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => null);

    if(!response.ok){
        const detail = data?.detail || "Errore richiesta pubblica.";
        throw new Error(detail);
    }

    return data;
}

function clearParentRequestForm(showMessage = true){
    const form = document.getElementById("parentRequestForm");

    if(form){
        form.reset();
    }

    if(showMessage){
        setRequestMessage("Modulo pulito.", "info");
    }
}

function setSubmitLoading(isLoading){
    const button = document.getElementById("submitRequestBtn");

    if(!button) return;

    button.disabled = isLoading;
    button.textContent = isLoading ? "Invio in corso..." : "Invia richiesta iscrizione";
}

function setRequestMessage(message, type){
    const box = document.getElementById("requestMessage");
    if(!box) return;

    box.textContent = message;
    box.className = `message ${type}`;
}
