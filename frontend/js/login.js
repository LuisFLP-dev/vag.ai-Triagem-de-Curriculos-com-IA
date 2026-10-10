const form = document.querySelector("#login-form");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const message = document.querySelector("#login-message");
const submitButton = form.querySelector('button[type = "submit"]')

form.addEventListener("submit", async function (event){
    event.preventDefault();

    if(submitButton.disabled) return;

    message.textContent = "Entrando..."
    submitButton.disabled = true;

    try{
        const body = new URLSearchParams({
            username: emailInput.value.trim(),
            password: passwordInput.value
        });

        const response = await fetch("/auth/login", {
            method: "POST",
            body: body
        });

        if(!response.ok){
            if(response.status === 400 || response.status === 401){
                throw new Error("E-mail ou senha incorretos.");
            }

            throw new Error("Não foi possível entrar. Tente novamente.");
        }

        const data = await response.json();

        if(!data.access_token){
            throw new Error("A API não retornou o token de acesso.");
        }

        sessionStorage.setItem("access_token", data.access_token);
        passwordInput.value = "";

        const profileResponse = await fetch("/auth/me", {
            headers:{
                Authorization: `Bearer ${data.access_token}`
            }
        });

        if(!profileResponse.ok){
            sessionStorage.removeItem("access_token");

            throw new Error(
                "Não foi possível consultar seu perfil. Entre novamente."
            );
            
        }

        const user = await profileResponse.json();

        const roleNames = {
            CANDIDATO: "Candidato",
            RECRUTADOR: "Recrutador",
            GERENTE_RH: "Gerente de RH"
        };

        const roleName = roleNames[user.role] ?? user.role;

        message.textContent =
            `Bem-vindo, ${user.full_name}! Seu perfil é: ${roleName}.`;

        window.location.assign("painel.html");

    }catch (error) {
        message.textContent = error instanceof TypeError
            ? "Não foi possível conectar à API. Confira se ela está rodando."
            : error.message;
    } finally {
        submitButton.disabled = false;
    }

});