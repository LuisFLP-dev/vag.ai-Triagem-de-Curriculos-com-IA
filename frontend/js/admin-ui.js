const AdminUI = {
    async request(url, method = "GET", body) {
        const token = sessionStorage.getItem("access_token");
        if (!token) {
            window.location.replace("index.html");
            throw new Error("Entre novamente para continuar.");
        }
        let response;
        try {
            response = await fetch(url, {
                method,
                headers: {
                    Authorization: `Bearer ${token}`,
                    ...(body ? { "Content-Type": "application/json" } : {})
                },
                ...(body ? { body: JSON.stringify(body) } : {})
            });
        } catch {
            throw new Error("Não foi possível conectar ao servidor. Confira os dados antes de tentar novamente.");
        }
        if (response.status === 401) {
            sessionStorage.removeItem("access_token");
            window.location.replace("index.html");
            throw new Error("Sua sessão expirou.");
        }
        if (response.status === 204) return null;
        const data = await response.json().catch(() => null);
        if (!response.ok) {
            const detail = data?.detail;
            throw new Error(typeof detail === "string" ? detail :
                response.status === 403 ? "Você não tem permissão para esta ação." :
                Array.isArray(detail) ? "Confira os campos preenchidos." : "Não foi possível concluir a operação.");
        }
        return data;
    },

    editor(kind, title, onSave) {
        const dialog = document.querySelector(`#${kind}-dialog`);
        const form = document.querySelector(`#${kind}-editor`);
        form.reset();
        document.querySelector(`#${kind}-dialog-title`).textContent = title;
        form.querySelector(".editor-message").textContent = "";
        let saving = false;
        form.querySelector(".cancel-editor").onclick = () => dialog.close();
        dialog.oncancel = event => { if (saving) event.preventDefault(); };
        form.onsubmit = async event => {
            event.preventDefault();
            if (saving || !form.reportValidity()) return;
            saving = true;
            const controls = [...form.elements];
            const disabled = controls.map(control => control.disabled);
            const data = new FormData(form);
            controls.forEach(control => { control.disabled = true; });
            const message = form.querySelector(".editor-message");
            message.textContent = "Salvando...";
            try {
                await onSave(data);
                dialog.close();
            } catch (error) {
                message.textContent = error.message;
            } finally {
                controls.forEach((control, index) => { control.disabled = disabled[index]; });
                saving = false;
            }
        };
        return { dialog, form };
    }
};
