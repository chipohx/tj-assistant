import React, { useState, useEffect } from "react";
import Header from "./components/Header.jsx";
import Main from "./components/Main.jsx";
import Registration from "./components/Registration.jsx";
import "./App.css";

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        // Проверяем токен при загрузке
        const token = localStorage.getItem("auth_token");
        if (token) {
            // Можно добавить проверку токена через API
            setIsLoggedIn(true);
        }
    }, []);

    const handleLogin = () => {
        setIsLoggedIn(true);
    };

    const handleLogout = () => {
        setIsLoggedIn(false);
        localStorage.removeItem("auth_token");
    };

    return (
        <div className="app">
            {isLoggedIn ? (
                <>
                    <Header onLogout={handleLogout} />
                    <Main />
                </>
            ) : (
                <Registration onLogin={handleLogin} />
            )}
        </div>
    );
}

export default App;