const pageMessage = document.querySelector("#page-message");
const retryButton = document.querySelector("#retry-button");
const logoutButton = document.querySelector("#logout-button");

function logout() {
    sessionStorage.removeItem("access_token");
    window.location.replace("index.html");
}

logoutButton.addEventListener("click", logout);
retryButton.addEventListener("click", loadManagerPage);

async function loadManagerPage() {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
        logout();
        return;
    }

    retryButton.hidden = true;
    pageMessage.hidden = false;
    pageMessage.textContent = "Verificando seu acesso...";
    document.querySelector("#users-section").hidden = true;
    document.querySelector("#users-nav-link").hidden = true;

    try {
        const response = await fetch("/auth/me", {
            headers: { Authorization: `Bearer ${token}` }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            throw new Error("Não foi possível verificar seu acesso.");
        }

        const user = await response.json();

        if (user.role !== "GERENTE_RH") {
            window.location.replace("painel.html");
            return;
        }

        document.querySelector("#users-nav-link").hidden = false;
        pageMessage.hidden = true;
        await loadUsers(user);
    } catch (error) {
        pageMessage.hidden = false;
        pageMessage.textContent = error instanceof TypeError
            ? "Não foi possível conectar ao servidor. Tente novamente."
            : error.message;
        retryButton.hidden = false;
    }
}

async function loadUsers(currentUser) {
    const section = document.querySelector("#users-section");
    const list = document.querySelector("#users-list");
    const feedback = document.querySelector("#users-message");
    const template = document.querySelector("#user-template");
    section.hidden = false;
    list.replaceChildren();
    feedback.textContent = "Carregando usuários...";
    document.querySelector("#create-user").onclick = () => openUserEditor(currentUser);
    try {
        const users = await AdminUI.request("/usuarios");
        const roles = { CANDIDATO: "Candidato", RECRUTADOR: "Recrutador", GERENTE_RH: "Gerente de RH" };
        for (const user of users) {
            const card = template.content.cloneNode(true);
            card.querySelector(".user-name").textContent = user.full_name;
            card.querySelector(".user-email").textContent = user.email;
            card.querySelector(".user-role").textContent = roles[user.role] ?? user.role;
            card.querySelector(".edit-user").onclick = () => openUserEditor(currentUser, user);
            const button = card.querySelector(".delete-user");
            const message = card.querySelector(".user-message");
            button.disabled = user.id === currentUser.id;
            if (button.disabled) message.textContent = "Sua própria conta não pode ser excluída.";
            button.onclick = () => deleteUser(currentUser, user, button, message);
            list.appendChild(card);
        }
        feedback.textContent = `${users.length} usuário(s) cadastrado(s).`;
    } catch (error) {
        feedback.textContent = error.message;
        retryButton.hidden = false;
    }
}

function openUserEditor(currentUser, user = null) {
    const { dialog, form } = AdminUI.editor("user", user ? "Editar usuário" : "Cadastrar usuário", async data => {
        const payload = { full_name: data.get("full_name").trim(), email: data.get("email").trim() };
        if (!payload.full_name) throw new Error("Informe o nome completo.");
        if (data.get("role")) payload.role = data.get("role");
        if (data.get("password")) payload.password = data.get("password");
        await AdminUI.request(user ? `/usuarios/${user.id}` : "/usuarios", user ? "PUT" : "POST", payload);
        if (user?.id === currentUser.id && payload.email !== currentUser.email) {
            logout();
            return;
        }
        await loadUsers(currentUser);
    });
    form.elements.full_name.value = user?.full_name ?? "";
    form.elements.email.value = user?.email ?? "";
    form.elements.password.value = "";
    form.elements.password.required = !user;
    form.elements.password.autocomplete = "new-password";
    form.elements.role.value = user?.role ?? "CANDIDATO";
    form.elements.role.disabled = user?.id === currentUser.id;
    form.querySelector('[type="submit"]').disabled = false;
    if (user?.id === currentUser.id) {
        form.querySelector(".editor-message").textContent = "Seu papel não pode ser alterado. Se mudar seu e-mail, entre novamente após salvar.";
    }
    dialog.showModal();
}

async function deleteUser(currentUser, user, button, feedback) {
    if (button.disabled || !window.confirm(`Excluir o usuário "${user.full_name}"? Esta ação não pode ser desfeita.`)) return;
    button.disabled = true;
    feedback.textContent = "Excluindo...";
    try {
        await AdminUI.request(`/usuarios/${user.id}`, "DELETE");
        await loadUsers(currentUser);
    } catch (error) {
        feedback.textContent = error.message;
    } finally {
        button.disabled = false;
    }
}

loadManagerPage();
