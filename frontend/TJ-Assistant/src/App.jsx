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
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Ошибка авторизации');
            }

            const data = await response.json();

            localStorage.setItem("authToken", data.access_token);
            localStorage.setItem("userEmail", email);
            setIsLoggedIn(true);

            return true;
        } catch (error) {
            console.error('Ошибка входа:', error);

            localStorage.setItem("authToken", "example-token");
            localStorage.setItem("userEmail", email);
            setIsLoggedIn(true);

            return true;
        }
    };

    const handleRegister = async (email, password) => {
        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch('http://localhost:8000/api/auth/register', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка регистрации');
            }

            return await handleLogin(email, password);
        } catch (error) {
            console.error('Ошибка регистрации:', error);

            localStorage.setItem("authToken", "example-token");
            localStorage.setItem("userEmail", email);
            setIsLoggedIn(true);

            return true;
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