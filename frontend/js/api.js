/*
  ClubIQ Segreteria - API Client
  V1.0
*/

const API_BASE_URL = "http://127.0.0.1:8000";

function getToken(){
    return localStorage.getItem("clubiq_token") || "";
}

function setToken(token){
    localStorage.setItem("clubiq_token", token);
}

function clearToken(){
    localStorage.removeItem("clubiq_token");
}

function isLoggedIn(){
    return !!getToken();
}

async function apiRequest(path, options = {}){
    const token = getToken();

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if(token){
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers
    });

    let data = null;

    try{
        data = await response.json();
    }catch(e){
        data = null;
    }

    if(!response.ok){
        const message = data?.detail || "Errore richiesta API";
        throw new Error(message);
    }

    return data;
}