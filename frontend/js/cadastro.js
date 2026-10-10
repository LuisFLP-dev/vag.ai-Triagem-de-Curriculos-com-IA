const form = document.querySelector("#register-form");
const nameInput = document.querySelector("#full_name");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const confirmationInput = document.querySelector("#confirm_password");
const message = document.querySelector("#register-message");
const button = form.querySelector('button[type="submit"]');

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (button.disabled) return;

    message.textContent = "";

    const fullName = nameInput.value.trim();

    if (!fullName) {
        message.textContent = "Informe seu nome completo.";
        nameInput.focus();
        return;
    }

    if (passwordInput.value !== confirmationInput.value) {
        message.textContent = "As senhas não coincidem.";
        confirmationInput.focus();
        return;
    }

    button.disabled = true;
    button.textContent = "Criando conta...";

    let registered = false;

    try {
        const response = await fetch("/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                full_name: fullName,
                email: emailInput.value.trim(),
                password: passwordInput.value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            let errorMessage =
                "Não foi possível criar a conta. Tente novamente.";

            if (response.status === 422) {
                errorMessage = "Confira o preenchimento dos campos.";
            } else if (
                response.status < 500 &&
                typeof data.detail === "string"
            ) {
                errorMessage = data.detail;
            }

            throw new Error(errorMessage);
        }

        registered = true;
        form.reset();

        message.textContent =
            "Conta criada com sucesso! Clique em Entrar abaixo para acessar.";

        button.textContent = "Conta criada";
    } catch (error) {
        message.textContent = error instanceof TypeError
            ? "Falha de conexão. Se o cadastro tiver sido concluído, você poderá entrar pela página de login."
            : error.message;
    } finally {
        if (!registered) {
            button.disabled = false;
            button.textContent = "Criar conta";
        }
    }
});

button.disabled = false;