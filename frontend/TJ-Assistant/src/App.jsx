import React, { useState } from "react";
import Header from "./components/Header.jsx";
import Main from "./components/Main.jsx";
import Registration from "./components/Registration.jsx";

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(() => {
        const token = localStorage.getItem("authToken");
        return !!token;
    });

    const handleLogin = async (email, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            console.log("📤 Отправка запроса на логин:", email);
            console.log("URL:", 'http://localhost:8000/api/auth/login');

            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            const responseText = await response.text();
            console.log("Статус ответа:", response.status);
            console.log("Текст ответа:", responseText);

            if (!response.ok) {
                let errorMessage = 'Ошибка авторизации';
                try {
                    const errorData = JSON.parse(responseText);
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    errorMessage = responseText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            const data = JSON.parse(responseText);
            console.log("✅ Данные ответа:", data);

            if (!data.access_token) {
                throw new Error('Токен не получен');
            }

            localStorage.setItem("authToken", data.access_token);
            localStorage.setItem("userEmail", email);
            setIsLoggedIn(true);

            return true;
        } catch (error) {
            console.error('❌ Ошибка входа:', error.message);
            alert(`Ошибка входа: ${error.message}`);
            return false;
        }
    };

    const handleRegister = async (email, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            console.log("📤 Отправка запроса на регистрацию:", email);
            console.log("URL:", 'http://localhost:8000/api/auth/register');

            const response = await fetch('http://localhost:8000/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            const responseText = await response.text();
            console.log("Статус ответа:", response.status);
            console.log("Текст ответа:", responseText);

            if (response.ok) {
                console.log("✅ Регистрация успешна, письмо отправлено");
                return { success: true, message: "На вашу почту отправлено письмо с подтверждением. Пожалуйста, проверьте вашу электронную почту." };
            } else {
                console.log("⚠️ Ответ от сервера не 200, но показываем стандартное сообщение");
                return { success: true, message: "Если email не был зарегистрирован ранее, на него отправлено письмо с подтверждением. Пожалуйста, проверьте вашу электронную почту." };
            }

        } catch (error) {
            console.error('❌ Ошибка регистрации:', error.message);
            return { success: true, message: "На вашу почту отправлено письмо с подтверждением. Пожалуйста, проверьте вашу электронную почту." };
        }
    };

    const handleLogout = () => {
        setIsLoggedIn(false);
        localStorage.removeItem("authToken");
        localStorage.removeItem("userEmail");
    };

    return (
        <>
            {isLoggedIn ? (
                <>
                    <Header
                        onLogout={handleLogout}
                        userEmail={localStorage.getItem("userEmail")}
                    />
                    <Main />
                </>
            ) : (
                <Registration onLogin={handleLogin} onRegister={handleRegister} />
            )}
        </>
    );
}

export default App;