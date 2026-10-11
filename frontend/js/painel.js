const message = document.querySelector("#panel-message");
const profileSection = document.querySelector("#profile-section");
const welcomeTitle = document.querySelector("#welcome-title");
const userRole = document.querySelector("#user-role");
const logoutButton = document.querySelector("#logout-button");

function logout() {
    sessionStorage.removeItem("access_token");
    window.location.replace("index.html");
}

logoutButton.addEventListener("click", logout);

async function loadJobs(user, applications) {
    const jobsList = document.querySelector("#jobs-list");
    const jobsMessage = document.querySelector("#jobs-message");
    const jobTemplate = document.querySelector("#job-template");

    jobsList.replaceChildren();
    jobsMessage.textContent = "Carregando oportunidades...";

    try {
        const response = await fetch("/vagas");

        if (!response.ok) {
            throw new Error("Não foi possível carregar as vagas.");
        }

        const jobs = await response.json();

        const openJobs = jobs.filter(function (job) {
            if (user.role === "CANDIDATO" && job.status !== "ABERTA") {
                return false;
            }

            if (user.role === "RECRUTADOR") {
                return job.recruiter_id === user.id;
            }

            return true;
        });

        if (openJobs.length === 0) {
            jobsMessage.textContent =
                "Não há vagas para exibir.";
            return;
        }

        for (const job of openJobs) {
            const card = jobTemplate.content.cloneNode(true);

            card.querySelector(".job-title").textContent = job.title;
            card.querySelector(".job-status").textContent =
                job.status === "ABERTA" ? "Vaga aberta" : "Vaga concluída";
            if (user.role === "GERENTE_RH") {
                card.querySelector(".job-actions").hidden = false;
                card.querySelector(".edit-job").addEventListener("click", () => openJobEditor(user, job));
                const deleteButton = card.querySelector(".delete-job");
                const feedback = card.querySelector(".job-admin-message");
                deleteButton.addEventListener("click", () => deleteJob(user, job, deleteButton, feedback));
            }

            card.querySelector(".job-description").textContent =
                job.description;

            const requirementsList =
                card.querySelector(".job-requirements");

            const requirements = job.requirements
                .split(";")
                .map(function (requirement) {
                    return requirement.trim();
                })
                .filter(function (requirement) {
                    return requirement !== "";
                });

            for (const requirement of requirements) {
                const item = document.createElement("li");

                item.textContent = requirement;
                requirementsList.appendChild(item);
            }

            const applicationForm = card.querySelector(".application-form");

            if (user.role === "CANDIDATO") {
                applicationForm.hidden = false;

                const button =
                    applicationForm.querySelector('button[type="submit"]');

                const fileInput =
                    applicationForm.querySelector('input[type="file"]');

                const statusMessage =
                    applicationForm.querySelector(".application-message");

                if (!Array.isArray(applications)) {
                    button.disabled = true;
                    fileInput.disabled = true;

                    statusMessage.textContent =
                        "Não foi possível conferir suas candidaturas. Atualize a página.";
                } else {
                    const alreadyApplied = applications.some(function (application) {
                        return application.vaga_id === job.id;
                    });

                    if (alreadyApplied) {
                        button.disabled = true;
                        fileInput.disabled = true;
                        button.textContent = "Candidatura enviada";

                        statusMessage.textContent =
                            "Você já se candidatou. Acompanhe em Minhas candidaturas.";
                    } else {
                        applicationForm.addEventListener("submit", function (event) {
                            event.preventDefault();

                            applyToJob(job.id, applicationForm);
                        });
                    }
                }
            }

            const viewCandidatesButton = card.querySelector(".view-candidates");

            if (
                user.role === "RECRUTADOR" ||
                user.role === "GERENTE_RH"
            ) {
                viewCandidatesButton.hidden = false;

                viewCandidatesButton.addEventListener("click", function () {
                    loadCandidates(job.id, job.title);
                });
            }

            jobsList.appendChild(card);
        }

        jobsMessage.textContent =
            `${openJobs.length} oportunidade(s) disponível(is).`;
    } catch (error) {
        jobsMessage.textContent = error instanceof TypeError
            ? "Não foi possível conectar ao servidor."
            : error.message;
    }
}

async function applyToJob(jobId, form) {
    const button = form.querySelector('button[type="submit"]');
    const fileInput = form.querySelector('input[type="file"]');
    const statusMessage = form.querySelector(".application-message");

    if (button.disabled) return;

    const token = sessionStorage.getItem("access_token");

    if (!token) {
        logout();
        return;
    }

    const file = fileInput.files[0];

    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
        statusMessage.textContent = "Selecione um arquivo PDF.";
        return;
    }

    const body = new FormData();
    body.append("file", file);

    let sent = false;

    button.disabled = true;
    fileInput.disabled = true;
    button.textContent = "Enviando...";

    statusMessage.textContent =
        "Estamos analisando seu currículo. Aguarde.";

    try {
        const response = await fetch(`/vagas/${jobId}/candidatar`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`
            },
            body: body
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            const detail = response.status < 500
                && typeof data.detail === "string"
                ? data.detail
                : "Não foi possível concluir a candidatura.";

            throw new Error(detail);
        }

        sent = true;

        statusMessage.textContent =
            "Candidatura enviada com sucesso! Aguarde a avaliação da equipe de RH.";

        button.textContent = "Candidatura enviada";
        await loadMyApplications();
    } catch (error) {
        statusMessage.textContent = error instanceof TypeError
            ? "Falha de conexão. Confira suas candidaturas antes de tentar novamente."
            : error.message;
    } finally {
        if (!sent) {
            button.disabled = false;
            fileInput.disabled = false;
            button.textContent = "Enviar candidatura";
        }
    }
}

async function loadProfile() {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
        logout();
        return;
    }

    try {
        const response = await fetch("/auth/me", {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            throw new Error(
                "Não foi possível carregar seu perfil. Atualize a página para tentar novamente."
            );
        }

        const user = await response.json();

        document.querySelector("#users-nav-link").hidden =
            user.role !== "GERENTE_RH";

        const roleNames = {
            CANDIDATO: "Candidato",
            RECRUTADOR: "Recrutador",
            GERENTE_RH: "Gerente de RH"
        };

        welcomeTitle.textContent = `Olá, ${user.full_name}!`;
        userRole.textContent = roleNames[user.role] ?? user.role;

        message.hidden = true;
        profileSection.hidden = false;

        let applications = [];

        if (user.role === "CANDIDATO") {
            applications = await loadMyApplications();
        }

        if (user.role === "GERENTE_RH") {
            document.querySelector("#jobs-title").textContent = "Gestão de vagas";
            const createButton = document.querySelector("#create-job");
            createButton.hidden = false;
            createButton.onclick = () => openJobEditor(user);
        }
        await loadJobs(user, applications);
    } catch (error) {
        message.textContent = error instanceof TypeError
            ? "Não foi possível conectar ao servidor. Confira a conexão e atualize a página."
            : error.message;
    }
}

async function loadMyApplications() {
    const section = document.querySelector("#applications-section");
    const list = document.querySelector("#applications-list");
    const feedback = document.querySelector("#applications-message");
    const template = document.querySelector("#application-template");

    const token = sessionStorage.getItem("access_token");

    if (!token) {
        logout();
        return;
    }

    section.hidden = false;
    list.replaceChildren();
    feedback.textContent = "Carregando suas candidaturas...";

    try {
        const response = await fetch("/minhas-candidaturas", {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            throw new Error("Não foi possível carregar suas candidaturas.");
        }

        const applications = await response.json();

        if (applications.length === 0) {
            feedback.textContent = "Você ainda não se candidatou a uma vaga.";
            return [];
        }

        const statusNames = {
            PENDENTE: "Em análise",
            CONTRATADO: "Contratado",
            REJEITADO: "Rejeitado"
        };

        for (const application of applications) {
            const card = template.content.cloneNode(true);

            card.querySelector(".application-title").textContent =
                application.titulo_vaga;

            card.querySelector(".application-status").textContent =
                statusNames[application.status_candidatura]
                ?? application.status_candidatura;

           
            const sentAt = new Date(`${application.data}Z`);

            card.querySelector(".application-date").textContent =
                sentAt.toLocaleDateString("pt-BR");

            list.appendChild(card);
        }

        feedback.textContent =
            `${applications.length} candidatura(s) enviada(s).`;
        return applications;
    } catch (error) {
        feedback.textContent = error instanceof TypeError
            ? "Não foi possível conectar ao servidor."
            : error.message;
    }
}

let candidatesRequestId = 0;

async function loadCandidates(jobId, jobTitle) {
    const section = document.querySelector("#candidates-section");
    const title = document.querySelector("#candidates-title");
    const feedback = document.querySelector("#candidates-message");
    const list = document.querySelector("#candidates-list");
    const template = document.querySelector("#candidate-template");

    const token = sessionStorage.getItem("access_token");

    if (!token) {
        logout();
        return;
    }

    const requestId = ++candidatesRequestId;

    section.hidden = false;
    title.textContent = `Candidatos — ${jobTitle}`;
    feedback.textContent = "Carregando candidatos...";
    list.replaceChildren();

    section.scrollIntoView({ behavior: "smooth", block: "start" });

    try {
        const response = await fetch(`/vagas/${jobId}/candidatos`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (requestId !== candidatesRequestId) return;

        if (response.status === 401) {
            logout();
            return;
        }

        if (response.status === 403) {
            throw new Error(
                "Você não tem permissão para consultar os candidatos desta vaga."
            );
        }

        if (!response.ok) {
            throw new Error("Não foi possível carregar os candidatos.");
        }

        const candidates = await response.json();

        if (requestId !== candidatesRequestId) return;

        if (candidates.length === 0) {
            feedback.textContent = "Esta vaga ainda não recebeu candidaturas.";
            return;
        }

        const statusNames = {
            PENDENTE: "Em análise",
            CONTRATADO: "Contratado",
            REJEITADO: "Rejeitado"
        };

        for (const candidate of candidates) {
            const card = template.content.cloneNode(true);

            card.querySelector(".candidate-name").textContent =
                candidate.candidato_nome;

            card.querySelector(".candidate-email").textContent =
                candidate.candidato_email;

            card.querySelector(".candidate-score").textContent =
                `${candidate.pontuacao_compatibilidade}/100`;

            card.querySelector(".candidate-status").textContent =
                statusNames[candidate.status_candidatura]
                ?? candidate.status_candidatura;

            card.querySelector(".candidate-feedback").textContent =
                candidate.parecer_ia;

            const article = card.querySelector("article");
            const hireButton = card.querySelector(".hire-button");
            const rejectButton = card.querySelector(".reject-button");

            hireButton.disabled =
                candidate.status_candidatura === "CONTRATADO";

            rejectButton.disabled =
                candidate.status_candidatura === "REJEITADO";

            hireButton.addEventListener("click", function () {
                updateApplicationStatus(candidate, "CONTRATADO", article);
            });

            rejectButton.addEventListener("click", function () {
                updateApplicationStatus(candidate, "REJEITADO", article);
            });

            list.appendChild(card);
        }

        feedback.textContent =
            `${candidates.length} candidatura(s), ordenada(s) por compatibilidade.`;
    } catch (error) {
        if (requestId !== candidatesRequestId) return;

        feedback.textContent = error instanceof TypeError
            ? "Não foi possível conectar ao servidor."
            : error.message;
    }
}

async function updateApplicationStatus(candidate, newStatus, article) {
    if (article.dataset.saving === "true") return;

    const token = sessionStorage.getItem("access_token");

    if (!token) {
        logout();
        return;
    }

    const statusNames = {
        PENDENTE: "Em análise",
        CONTRATADO: "Contratado",
        REJEITADO: "Rejeitado"
    };

    const confirmed = window.confirm(
        `Marcar ${candidate.candidato_nome} como ${statusNames[newStatus]}?`
    );

    if (!confirmed) return;

    const hireButton = article.querySelector(".hire-button");
    const rejectButton = article.querySelector(".reject-button");
    const feedback = article.querySelector(".decision-message");
    const statusLabel = article.querySelector(".candidate-status");

    article.dataset.saving = "true";
    hireButton.disabled = true;
    rejectButton.disabled = true;
    feedback.textContent = "Salvando decisão...";

    try {
        const response = await fetch(
            `/candidaturas/${candidate.candidatura_id}/status`,
            {
                method: "PATCH",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    status: newStatus
                })
            }
        );

        if (response.status === 401) {
            logout();
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            const errorMessage =
                response.status < 500 && typeof data.detail === "string"
                    ? data.detail
                    : "Não foi possível atualizar a candidatura.";

            throw new Error(errorMessage);
        }

        candidate.status_candidatura = data.novo_status;

        statusLabel.textContent =
            statusNames[data.novo_status] ?? data.novo_status;

        feedback.textContent = "Decisão salva com sucesso.";
    } catch (error) {
        feedback.textContent = error instanceof TypeError
            ? "Falha de conexão. Consulte os candidatos novamente para confirmar o status."
            : error.message;
    } finally {
        article.dataset.saving = "false";

        hireButton.disabled =
            candidate.status_candidatura === "CONTRATADO";

        rejectButton.disabled =
            candidate.status_candidatura === "REJEITADO";
    }
}

loadProfile();

let jobEditorRequestId = 0;

async function openJobEditor(currentUser, job = null) {
    const requestId = ++jobEditorRequestId;
    const { dialog, form } = AdminUI.editor("job", job ? "Editar vaga" : "Cadastrar vaga", async data => {
        const payload = {
            title: data.get("title").trim(),
            description: data.get("description").trim(),
            requirements: data.get("requirements").split(/\r?\n/).map(value => value.trim()).filter(Boolean),
            recruiter_id: Number(data.get("recruiter_id"))
        };
        if (!payload.title || !payload.description || !payload.requirements.length || !payload.recruiter_id) {
            throw new Error("Preencha o título, a descrição, os requisitos e o recrutador.");
        }
        if (job) payload.status = data.get("status");
        await AdminUI.request(job ? `/vagas/${job.id}` : "/vagas", job ? "PUT" : "POST", payload);
        document.querySelector("#candidates-section").hidden = true;
        candidatesRequestId += 1;
        await loadJobs(currentUser, []);
    });
    form.elements.title.value = job?.title ?? "";
    form.elements.description.value = job?.description ?? "";
    form.elements.requirements.value = job?.requirements.split(";").join("\n") ?? "";
    form.elements.status.value = job?.status ?? "ABERTA";
    form.elements.status.disabled = !job;
    const recruiterSelect = form.elements.recruiter_id;
    recruiterSelect.replaceChildren();
    const submit = form.querySelector('[type="submit"]');
    submit.disabled = true;
    dialog.showModal();
    form.querySelector(".editor-message").textContent = "Carregando recrutadores...";
    try {
        const users = await AdminUI.request("/usuarios");
        if (requestId !== jobEditorRequestId) return;
        for (const user of users.filter(user => user.role === "RECRUTADOR")) {
            recruiterSelect.add(new Option(`${user.full_name} — ${user.email}`, user.id));
        }
        if (!recruiterSelect.options.length) throw new Error("Cadastre um recrutador em Usuários e papéis antes de criar uma vaga.");
        if (job) recruiterSelect.value = String(job.recruiter_id);
        form.querySelector(".editor-message").textContent = "";
        submit.disabled = false;
    } catch (error) {
        if (requestId !== jobEditorRequestId) return;
        form.querySelector(".editor-message").textContent = error.message;
    }
}

async function deleteJob(currentUser, job, button, feedback) {
    if (button.disabled || !window.confirm(`Excluir a vaga "${job.title}"? Todas as candidaturas vinculadas também serão removidas. Esta ação não pode ser desfeita.`)) return;
    button.disabled = true;
    feedback.textContent = "Excluindo...";
    try {
        await AdminUI.request(`/vagas/${job.id}`, "DELETE");
        candidatesRequestId += 1;
        document.querySelector("#candidates-section").hidden = true;
        await loadJobs(currentUser, []);
    } catch (error) {
        feedback.textContent = error.message;
    } finally {
        button.disabled = false;
    }
}
